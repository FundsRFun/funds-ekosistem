from django.shortcuts import render, redirect
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Tabungan
import pandas as pd

# Dashboard tabungan
def index_tabungan(request):
    filter_cabang = request.GET.get('nama_cabang')
    filter_uker = request.GET.get('nama_uker')

    data = Tabungan.objects.all()

    # Filter data berdasarkan cabang dan uker
    if filter_cabang:
        data = data.filter(nama_cabang=filter_cabang)
    if filter_uker:
        data = data.filter(nama_uker=filter_uker)

    # Daftar dropdown cabang dan uker
    cabang_list = (
        Tabungan.objects.exclude(nama_cabang__isnull=True)
        .exclude(nama_cabang__exact="")
        .values_list("nama_cabang", flat=True)
        .distinct()
        .order_by("nama_cabang")
    )

    if filter_cabang:
        uker_list = (
            Tabungan.objects.filter(nama_cabang=filter_cabang)
            .exclude(nama_uker__isnull=True)
            .exclude(nama_uker__exact="")
            .values_list("nama_uker", flat=True)
            .distinct()
            .order_by("nama_uker")
        )
    else:
        uker_list = []

    # -------------------------------
    # Grafik Line Chart
    # -------------------------------
    chart_labels, chart_values = [], []

    if filter_cabang and not filter_uker:
        grafik = (
            Tabungan.objects.filter(nama_cabang=filter_cabang)
            .values("tanggal_posisi")
            .annotate(total_saldo=Sum("saldo"))
            .order_by("tanggal_posisi")
        )
        chart_labels = [g["tanggal_posisi"].strftime("%Y-%m-%d") for g in grafik]
        chart_values = [float(g["total_saldo"] or 0) for g in grafik]

        # Tabel semua uker di cabang tersebut
        tabel_data = (
            Tabungan.objects.filter(nama_cabang=filter_cabang)
            .values("nama_cabang", "nama_uker", "tanggal_posisi", "saldo")
            .order_by("nama_uker", "-tanggal_posisi")
        )

    elif filter_cabang and filter_uker:
        grafik = (
            Tabungan.objects.filter(nama_cabang=filter_cabang, nama_uker=filter_uker)
            .values("tanggal_posisi")
            .annotate(total_saldo=Sum("saldo"))
            .order_by("tanggal_posisi")
        )
        chart_labels = [g["tanggal_posisi"].strftime("%Y-%m-%d") for g in grafik]
        chart_values = [float(g["total_saldo"] or 0) for g in grafik]

        # Tabel hanya uker tersebut
        tabel_data = (
            Tabungan.objects.filter(nama_cabang=filter_cabang, nama_uker=filter_uker)
            .values("nama_cabang", "nama_uker", "tanggal_posisi", "saldo")
            .order_by("-tanggal_posisi")
        )
    else:
        tabel_data = []

    context = {
        "cabang_list": cabang_list,
        "uker_list": uker_list,
        "filter_cabang": filter_cabang,
        "filter_uker": filter_uker,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "tabel_data": tabel_data,
    }

    return render(request, "tabungan/index_tabungan.html", context)

# Data tabel semua tabungan
def data_tabungan(request):
    query = request.GET.get('q', '')
    tabungan_list = Tabungan.objects.all()

    if query:
        tabungan_list = tabungan_list.filter(
            Q(nama_cabang__icontains=query) |
            Q(nama_uker__icontains=query) |
            Q(segmentasi__icontains=query) |
            Q(jenis_produk__icontains=query) |
            Q(group_product__icontains=query) |
            Q(flag_posisi__icontains=query) |
            Q(nama_region__icontains=query)
        )

    paginator = Paginator(tabungan_list, 20)  # 20 data per halaman
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tabungan/data_tabungan.html', {
        'data': page_obj,
        'query': query
    })


# Upload file CSV/Excel tabungan
def upload_tabungan(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        # baca file (csv/xlsx)
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            for _, row in df.iterrows():
                Tabungan.objects.create(
                    nama_cabang=row.get('nama_cabang'),
                    nama_uker=row.get('nama_uker'),
                    segmentasi=row.get('segmentasi'),
                    jenis_produk=row.get('jenis_produk'),
                    group_product=row.get('group_product'),
                    tanggal_posisi=row.get('tanggal_posisi'),
                    flag_posisi=row.get('flag_posisi'),
                    nama_region=row.get('nama_region'),
                    segmentasi_bpr=row.get('segmentasi_bpr'),
                    jumlah_rekening=row.get('jumlah_rekening'),
                    saldo=row.get('saldo'),
                )
            messages.success(request, "Data tabungan berhasil diupload!")
            return redirect('data_tabungan')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {e}")
            return redirect('upload_tabungan')

    return render(request, 'tabungan/upload_tabungan.html')