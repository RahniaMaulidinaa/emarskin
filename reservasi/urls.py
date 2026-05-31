from django.urls import path
from . import views

urlpatterns = [
    path('', views.beranda, name='beranda'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reservasi/', views.reservasi_form, name='reservasi_form'),
    path('reservasi/slots/', views.get_slots_ajax, name='get_slots_ajax'),  
    path('status/', views.status_riwayat, name='status_riwayat'),

    # Admin panel
    path('admin-panel/', views.dashboard_admin, name='dashboard_admin'),
    path('admin-panel/reservasi/', views.kelola_reservasi, name='kelola_reservasi'),
    path('admin-panel/reservasi/<int:pk>/konfirmasi/', views.konfirmasi_reservasi, name='konfirmasi_reservasi'),
    path('admin-panel/reservasi/<int:pk>/batalkan/', views.batalkan_reservasi, name='batalkan_reservasi'),
    path('admin-panel/reservasi/<int:pk>/selesai/', views.selesai_reservasi, name='selesai_reservasi'),
    path('admin-panel/laporan/', views.laporan_reservasi, name='laporan_reservasi'),
]