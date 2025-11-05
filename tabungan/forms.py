from django import forms

class UploadForm(forms.Form):
    file = forms.FileField(
        label="Pilih file data",
        help_text="Format didukung: CSV, Excel, TXT, atau file lain yang bisa dibaca otomatis.",
        widget=forms.ClearableFileInput(attrs={
            "accept": ".csv,.xls,.xlsx,.txt,.tsv"  # kamu bisa hapus kalau ingin betul-betul 'semua file'
        })
    )