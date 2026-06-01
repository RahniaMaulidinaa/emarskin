from django.db import models
from django.contrib.auth.models import User


class Pelanggan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    no_telepon = models.CharField(max_length=20)
    alamat = models.TextField()

    def __str__(self):
        return self.nama


class Treatment(models.Model):
    nama_treatment = models.CharField(max_length=100)
    deskripsi = models.TextField()
    durasi = models.IntegerField(help_text="Durasi dalam menit")
    harga = models.DecimalField(max_digits=10, decimal_places=0)

    gambar = models.ImageField(
        upload_to='treatments/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nama_treatment


class Reservasi(models.Model):
    STATUS_CHOICES = [
        ('menunggu', 'Menunggu'),
        ('terkonfirmasi', 'Terkonfirmasi'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    ]
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE)
    tanggal_reservasi = models.DateField()
    jam_reservasi = models.TimeField()
    waktu_pesan = models.DateTimeField(auto_now_add=True)
    status_reservasi = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='menunggu'
    )
    nomor_antrian = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['waktu_pesan']

    def __str__(self):
        return f"#{self.nomor_antrian} - {self.pelanggan.nama} - {self.tanggal_reservasi}"

    def save(self, *args, **kwargs):
        if not self.nomor_antrian:
            existing = Reservasi.objects.filter(
                tanggal_reservasi=self.tanggal_reservasi
            ).count()
            self.nomor_antrian = existing + 1
        super().save(*args, **kwargs)