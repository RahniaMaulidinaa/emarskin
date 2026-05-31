from django.contrib import admin
from .models import Pelanggan, Treatment, Reservasi


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['nama_treatment', 'durasi', 'harga']


@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    list_display = ['nama', 'no_telepon', 'user']


@admin.register(Reservasi)
class ReservasiAdmin(admin.ModelAdmin):
    list_display = [
        'nomor_antrian', 'pelanggan', 'treatment',
        'tanggal_reservasi', 'jam_reservasi',
        'status_reservasi', 'waktu_pesan'
    ]
    list_filter = ['status_reservasi', 'tanggal_reservasi']
    ordering = ['waktu_pesan']