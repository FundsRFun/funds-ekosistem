from django.shortcuts import render, redirect
from django.db.models import Q, Sum, Max
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Simpanan
from datetime import datetime
from datetime import timedelta
from django.db.models.functions import TruncMonth
import pandas as pd
import calendar
import re

# Data tabel semua tabungan
def index_simpanan(request):
    # Ambil filter GET
    cabang = request.GET.get('cabang', 'semua')
    uker = request.GET.get('uker', 'semua')
    tanggal_filter = request.GET.getlist('tanggal[]')  # multi checklist

    qs = Simpanan.objects.all()

    if cabang != 'semua':
        qs = qs.filter(nama_cabang=cabang)    
    if uker != 'semua':
        qs = qs.filter(nama_uker=uker)

    # filter tanggal multi pilihan
    if tanggal_filter and "semua" not in tanggal_filter:
        qs = qs.filter(tanggal_posisi__in=tanggal_filter)

    # === DATA CHART DEFAULT (per bulan) ===
    data_chart = (
        qs.annotate(bln=TruncMonth('tanggal_posisi'))
        .values('bln','jenis_produk')
        .annotate(total=Sum('saldo'))
        .order_by('bln')
    )

    # Buat label bulan
    months_order = sorted(list({(d['bln'].year, d['bln'].month) for d in data_chart if d['bln']}))
    default_labels = [f"{calendar.month_abbr[m]} {y}" for (y, m) in months_order]

    produk_list = ['Tabungan', 'Giro', 'Deposito']
    default_chart = {p: [0]*len(default_labels) for p in produk_list}

    for d in data_chart:
        if d['bln']:
            key = f"{calendar.month_abbr[d['bln'].month]} {d['bln'].year}"
            idx = default_labels.index(key)
            jenis = d['jenis_produk'].capitalize()
            default_chart[jenis][idx] = float(d['total'] or 0)/1_000_000_000

    # === DATA RAW PER TANGGAL (untuk dropdown filter) ===
    raw_data = {}
    for row in Simpanan.objects.all():
        t = row.tanggal_posisi.strftime('%Y-%m-%d')
        if t not in raw_data: 
            raw_data[t] = {"Tabungan": 0, "Giro": 0, "Deposito": 0}
        raw_data[t][row.jenis_produk.capitalize()] += float(row.saldo or 0) / 1_000_000_000

    # Dropdown source
    cabang_list  = Simpanan.objects.values_list('nama_cabang', flat=True).distinct()
    uker_list    = Simpanan.objects.values_list('nama_uker', flat=True).distinct()
    tanggal_list = Simpanan.objects.values_list('tanggal_posisi', flat=True).distinct().order_by('tanggal_posisi')

    context = {
        "cabang_list": cabang_list,
        "uker_list": uker_list,
        "tanggal_list": tanggal_list,
        "filters": {
            "cabang": cabang,
            "uker": uker,
            "tanggal": tanggal_filter
        },

        # chart raw untuk js dynamic
        "default_labels": default_labels,
        "default_chart": default_chart,
        "raw_data": raw_data,
    }
    return render(request, "simpanan/index_simpanan.html", context)

def data_simpanan(request):
    query = request.GET.get('q', '')
    simpanan_list = Simpanan.objects.all()

    # Filter pencarian
    if query:
        simpanan_list = simpanan_list.filter(
            Q(nama_cabang__icontains=query) |
            Q(nama_uker__icontains=query) |
            Q(segmentasi__icontains=query) |
            Q(jenis_produk__icontains=query) |
            Q(group_product__icontains=query) |
            Q(flag_posisi__icontains=query) |
            Q(nama_region__icontains=query)
        )

    # Konversi saldo ke jutaan (2 desimal)
    for s in simpanan_list:
        try:
            s.saldo_juta = round(float(s.saldo or 0) / 1_000)
        except:
            s.saldo_juta = 0.00

    # Pagination
    paginator = Paginator(simpanan_list, 20)  # 20 data per halaman
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Kirim ke template
    return render(request, 'simpanan/data_simpanan.html', {
        'data': page_obj,
        'query': query
    })

# --- Helper Functions ---
def _to_int_safe(val):
    """Konversi ke int dengan aman."""
    try:
        if pd.isna(val) or str(val).strip() == "":
            return None
        return int(float(val))
    except Exception:
        return None

def _to_float_safe(val):
    """Konversi ke float dengan aman."""
    try:
        if pd.isna(val) or str(val).strip() == "":
            return None
        return float(val)
    except Exception:
        return None

# --- Upload File Simpanan ---
def upload_simpanan(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        try:
            # === Baca file (CSV / Excel) ===
            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Normalisasi nama kolom ke huruf kecil semua
            df.columns = [col.strip().lower() for col in df.columns]

            # Pastikan kolom wajib tersedia
            required_cols = [
                "nama cabang",
                "nama uker",
                "jenis produk",
                "month, day, year of posisi",
                "saldo"
            ]
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Kolom '{col}' tidak ditemukan di file Excel!")

            # Loop setiap baris
            for _, row in df.iterrows():
                # === Konversi kolom tanggal ===
                tanggal_raw = row.get("month, day, year of posisi")
                tanggal_posisi = None
                try:
                    if pd.notna(tanggal_raw) and str(tanggal_raw).strip() != "":
                        tanggal_posisi = pd.to_datetime(tanggal_raw).date()
                except Exception:
                    tanggal_posisi = None

                # === Jumlah Rekening & Saldo ===
                jumlah_rekening_val = _to_int_safe(row.get("jumlah rekening"))
                saldo_val = _to_float_safe(row.get("saldo"))

                # === Flag Posisi ===
                flag_raw = row.get("flag posisi")
                flag_val = " " if pd.isna(flag_raw) or str(flag_raw).strip() == "" else str(flag_raw).strip()

                # === Simpan ke Database ===
                Simpanan.objects.create(
                    nama_cabang=row.get("nama cabang", "") or "",
                    nama_uker=row.get("nama uker", "") or "",
                    jenis_produk=row.get("jenis produk", "") or "",
                    segmentasi=row.get("segmentasi", "") or "",
                    group_product=row.get("group product", "") or "",
                    tanggal_posisi=tanggal_posisi,
                    flag_posisi=flag_val,
                    nama_region=row.get("nama region", "") or "",
                    segmentasi_bpr=row.get("segmentasi bpr", "") or "",
                    jumlah_rekening=jumlah_rekening_val,
                    saldo=saldo_val or 0.0,
                )

            messages.success(request, "✅ Data simpanan berhasil diupload!")
            return redirect("data_simpanan")

        except Exception as e:
            messages.error(request, f"❌ Terjadi kesalahan saat upload: {e}")
            return redirect("data_simpanan")

    return render(request, "simpanan/upload_simpanan.html")

def hapus_semua_simpanan(request):
    if request.method == "POST":
        try:
            total = Simpanan.objects.count()
            Simpanan.objects.all().delete()
            messages.warning(request, f"⚠️ Semua data simpanan ({total} baris) telah dihapus!")
        except Exception as e:
            messages.error(request, f"❌ Gagal menghapus semua data: {e}")
        return redirect("data_simpanan")

    # Jika bukan POST, kembalikan ke halaman utama
    messages.info(request, "Tidak ada data yang dihapus.")
    return redirect("data_simpanan")