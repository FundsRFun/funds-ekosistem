from django.db import models

# Create your models here.
class Simpanan(models.Model):
    nama_cabang = models.CharField(max_length=100)
    nama_uker = models.CharField(max_length=100)
    segmentasi = models.CharField(max_length=100, null=True, blank=True)
    jenis_produk = models.CharField(max_length=100, null=True, blank=True)
    group_product = models.CharField(max_length=100, null=True, blank=True)
    tanggal_posisi = models.DateField(null=True, blank=True)
    flag_posisi = models.CharField(max_length=100, null=True, blank=True)
    nama_region = models.CharField(max_length=100, null=True, blank=True)
    segmentasi_bpr = models.CharField(max_length=100, null=True, blank=True)
    jumlah_rekening = models.IntegerField(null=True, blank=True)
    saldo = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)