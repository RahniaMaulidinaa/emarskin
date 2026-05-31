from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Pelanggan, Reservasi


class RegisterForm(UserCreationForm):
    nama = forms.CharField(
        max_length=100,
        label="Nama Lengkap",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    no_telepon = forms.CharField(
        max_length=20,
        label="No. Telepon",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    alamat = forms.CharField(
        label="Alamat",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=commit)
        Pelanggan.objects.create(
            user=user,
            nama=self.cleaned_data['nama'],
            no_telepon=self.cleaned_data['no_telepon'],
            alamat=self.cleaned_data['alamat'],
        )
        return user


class ReservasiForm(forms.ModelForm):
    class Meta:
        model = Reservasi
        fields = ['treatment', 'tanggal_reservasi', 'jam_reservasi']
        widgets = {
            'treatment': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_reservasi': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'jam_reservasi': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'}
            ),
        }