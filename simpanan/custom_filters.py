from django import template

register = template.Library()

@register.filter
def juta(value):
    """Ubah angka menjadi format jutaan dengan dua desimal"""
    try:
        val = float(value) / 1_000_000
        return f"{val:,.2f} Jt"
    except (TypeError, ValueError):
        return "0.00 Jt"
