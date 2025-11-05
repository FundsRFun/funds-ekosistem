from django.urls import path
from . import views

urlpatterns = [
    path('index_simpanan/', views.index_simpanan, name='index_simpanan'),
    path('data_simpanan/', views.data_simpanan, name='data_simpanan'),
    path('upload_simpanan/', views.upload_simpanan, name='upload_simpanan'),
path('hapus_semua_simpanan/', views.hapus_semua_simpanan, name='hapus_semua_simpanan'),
]
