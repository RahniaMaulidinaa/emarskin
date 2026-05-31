from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time, timedelta, date
from .models import Pelanggan, Reservasi, Treatment
from .forms import RegisterForm, ReservasiForm
import json


def is_admin(user):
    return user.is_staff


# ── PUBLIK ──────────────────────────────────────────

def beranda(request):
    treatments = Treatment.objects.all()
    return render(request, 'reservasi/beranda.html', {'treatments': treatments})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Akun berhasil dibuat!')
            return redirect('reservasi_form')
    else:
        form = RegisterForm()
    return render(request, 'reservasi/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('dashboard_admin')
            return redirect('reservasi_form')
        else:
            messages.error(request, 'Username atau password salah.')
    return render(request, 'reservasi/login.html')


def logout_view(request):
    logout(request)
    return redirect('beranda')


# ── HELPER: generate slot jam ────────────────────────

def get_slot_jam(tanggal_str):
    """
    Generate slot jam 09:00 - 16:30 dengan interval 30 menit.
    Tandai slot yang sudah penuh berdasarkan reservasi aktif.
    Close order: 16:30 (slot terakhir 16:00, selesai 16:30).
    """
    slots = []
    jam_mulai = time(9, 0)
    jam_close = time(16, 30)

    # Buat semua slot 30 menit
    current = datetime.combine(date.today(), jam_mulai)
    end = datetime.combine(date.today(), jam_close)

    while current.time() <= time(16, 0):  # slot terakhir 16:00
        slots.append(current.time())
        current += timedelta(minutes=30)

    # Cek slot yang sudah dipesan pada tanggal tersebut
    if tanggal_str:
        try:
            tgl = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            reservasi_aktif = Reservasi.objects.filter(
                tanggal_reservasi=tgl,
                status_reservasi__in=['menunggu', 'terkonfirmasi']
            ).values_list('jam_reservasi', flat=True)
            penuh = [j for j in reservasi_aktif]
        except:
            penuh = []
    else:
        penuh = []

    # Format slot
    hasil = []
    for s in slots:
        hasil.append({
            'jam': s.strftime('%H:%M'),
            'penuh': s in penuh,
        })
    return hasil


# ── PELANGGAN ────────────────────────────────────────

@login_required
def reservasi_form(request):
    try:
        pelanggan = request.user.pelanggan
    except Pelanggan.DoesNotExist:
        messages.error(request, 'Profil tidak ditemukan.')
        return redirect('beranda')

    treatments = Treatment.objects.all()
    today = date.today().strftime('%Y-%m-%d')
    tanggal_dipilih = request.GET.get('tanggal', today)
    slots = get_slot_jam(tanggal_dipilih)

    if request.method == 'POST':
        treatment_id = request.POST.get('treatment')
        tanggal = request.POST.get('tanggal_reservasi')
        jam = request.POST.get('jam_reservasi')

        # Validasi close order 16:30
        try:
            jam_obj = datetime.strptime(jam, '%H:%M').time()
        except:
            messages.error(request, 'Format jam tidak valid.')
            return redirect('reservasi_form')

        if jam_obj > time(16, 0):
            messages.error(request, 'Maaf, pemesanan terakhir jam 16:00 (close order 16:30).')
            return redirect('reservasi_form')

        # Cek apakah slot sudah penuh
        tgl_obj = datetime.strptime(tanggal, '%Y-%m-%d').date()
        sudah_penuh = Reservasi.objects.filter(
            tanggal_reservasi=tgl_obj,
            jam_reservasi=jam_obj,
            status_reservasi__in=['menunggu', 'terkonfirmasi']
        ).exists()

        if sudah_penuh:
            messages.error(request, f'Maaf, slot jam {jam} pada tanggal tersebut sudah penuh. Pilih jam lain.')
            slots = get_slot_jam(tanggal)
            return render(request, 'reservasi/reservasi_form.html', {
                'treatments': treatments,
                'slots': slots,
                'tanggal_dipilih': tanggal,
                'today': today,
            })

        try:
            treatment = Treatment.objects.get(id=treatment_id)
        except Treatment.DoesNotExist:
            messages.error(request, 'Treatment tidak ditemukan.')
            return redirect('reservasi_form')

        reservasi = Reservasi(
            pelanggan=pelanggan,
            treatment=treatment,
            tanggal_reservasi=tgl_obj,
            jam_reservasi=jam_obj,
        )
        reservasi.save()
        messages.success(
            request,
            f'✅ Reservasi berhasil! No. antrian kamu: #{reservasi.nomor_antrian} — {treatment.nama_treatment} jam {jam}'
        )
        return redirect('status_riwayat')

    return render(request, 'reservasi/reservasi_form.html', {
        'treatments': treatments,
        'slots': slots,
        'tanggal_dipilih': tanggal_dipilih,
        'today': today,
    })


@login_required
def get_slots_ajax(request):
    """AJAX endpoint untuk refresh slot saat tanggal berubah"""
    tanggal = request.GET.get('tanggal', '')
    slots = get_slot_jam(tanggal)
    return JsonResponse({'slots': slots})


@login_required
def status_riwayat(request):
    try:
        pelanggan = request.user.pelanggan
    except Pelanggan.DoesNotExist:
        return redirect('beranda')
    reservasis = Reservasi.objects.filter(
        pelanggan=pelanggan
    ).order_by('-waktu_pesan')
    return render(request, 'reservasi/status_riwayat.html', {'reservasis': reservasis})


# ── ADMIN ────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dashboard_admin(request):
    total = Reservasi.objects.count()
    menunggu = Reservasi.objects.filter(status_reservasi='menunggu').count()
    terkonfirmasi = Reservasi.objects.filter(status_reservasi='terkonfirmasi').count()
    pelanggan_count = Pelanggan.objects.count()
    antrian = Reservasi.objects.filter(
        status_reservasi='menunggu'
    ).order_by('waktu_pesan')[:10]
    return render(request, 'reservasi/admin_panel/dashboard.html', {
        'total': total,
        'menunggu': menunggu,
        'terkonfirmasi': terkonfirmasi,
        'pelanggan_count': pelanggan_count,
        'antrian_hari_ini': antrian,
    })


@login_required
@user_passes_test(is_admin)
def kelola_reservasi(request):
    reservasis = Reservasi.objects.all().order_by('waktu_pesan')
    return render(request, 'reservasi/admin_panel/kelola_reservasi.html', {
        'reservasis': reservasis
    })


@login_required
@user_passes_test(is_admin)
def konfirmasi_reservasi(request, pk):
    reservasi = get_object_or_404(Reservasi, pk=pk)
    reservasi.status_reservasi = 'terkonfirmasi'
    reservasi.save()
    messages.success(request, f'Reservasi #{reservasi.nomor_antrian} dikonfirmasi.')
    return redirect('kelola_reservasi')


@login_required
@user_passes_test(is_admin)
def batalkan_reservasi(request, pk):
    reservasi = get_object_or_404(Reservasi, pk=pk)
    reservasi.status_reservasi = 'dibatalkan'
    reservasi.save()
    messages.warning(request, f'Reservasi #{reservasi.nomor_antrian} dibatalkan.')
    return redirect('kelola_reservasi')


@login_required
@user_passes_test(is_admin)
def selesai_reservasi(request, pk):
    reservasi = get_object_or_404(Reservasi, pk=pk)
    reservasi.status_reservasi = 'selesai'
    reservasi.save()
    messages.success(request, f'Reservasi #{reservasi.nomor_antrian} ditandai selesai.')
    return redirect('kelola_reservasi')


@login_required
@user_passes_test(is_admin)
def laporan_reservasi(request):
    periode = request.GET.get('periode', 'harian')
    tanggal_str = request.GET.get('tanggal', date.today().strftime('%Y-%m-%d'))
    
    try:
        tanggal_ref = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
    except:
        tanggal_ref = date.today()

    # Tentukan rentang tanggal berdasarkan periode
    if periode == 'harian':
        tgl_mulai = tanggal_ref
        tgl_selesai = tanggal_ref
        label_periode = f"Harian — {tanggal_ref.strftime('%d %B %Y')}"

    elif periode == 'mingguan':
        # Senin s/d Minggu dari minggu yang dipilih
        tgl_mulai = tanggal_ref - timedelta(days=tanggal_ref.weekday())
        tgl_selesai = tgl_mulai + timedelta(days=6)
        label_periode = f"Mingguan — {tgl_mulai.strftime('%d %b')} s/d {tgl_selesai.strftime('%d %b %Y')}"

    elif periode == 'bulanan':
        import calendar
        tgl_mulai = tanggal_ref.replace(day=1)
        last_day = calendar.monthrange(tanggal_ref.year, tanggal_ref.month)[1]
        tgl_selesai = tanggal_ref.replace(day=last_day)
        label_periode = f"Bulanan — {tanggal_ref.strftime('%B %Y')}"

    else:
        tgl_mulai = tgl_selesai = tanggal_ref
        label_periode = tanggal_ref.strftime('%d %B %Y')

    # Query data
    reservasis = Reservasi.objects.filter(
        tanggal_reservasi__gte=tgl_mulai,
        tanggal_reservasi__lte=tgl_selesai,
    ).order_by('waktu_pesan')

    total          = reservasis.count()
    total_menunggu = reservasis.filter(status_reservasi='menunggu').count()
    total_konfirm  = reservasis.filter(status_reservasi='terkonfirmasi').count()
    total_selesai  = reservasis.filter(status_reservasi='selesai').count()
    total_batal    = reservasis.filter(status_reservasi='dibatalkan').count()

    # Rekap per treatment
    rekap_treatment = reservasis.values(
        'treatment__nama_treatment'
    ).annotate(jumlah=Count('id')).order_by('-jumlah')

    return render(request, 'reservasi/admin_panel/laporan.html', {
        'reservasis':        reservasis,
        'periode':           periode,
        'tanggal_ref':       tanggal_ref.strftime('%Y-%m-%d'),
        'label_periode':     label_periode,
        'tgl_mulai':         tgl_mulai,
        'tgl_selesai':       tgl_selesai,
        'total':             total,
        'total_menunggu':    total_menunggu,
        'total_konfirm':     total_konfirm,
        'total_selesai':     total_selesai,
        'total_batal':       total_batal,
        'rekap_treatment':   rekap_treatment,
        'today':             date.today().strftime('%Y-%m-%d'),
    })