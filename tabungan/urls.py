from django.urls import path
from . import views

urlpatterns = [
    path('index_tabungan/', views.index_tabungan, name='index_tabungan'),
    path('data_tabungan/', views.data_tabungan, name='data_tabungan'),
    path('upload_tabungan/', views.upload_tabungan, name='upload_tabungan'),
]
