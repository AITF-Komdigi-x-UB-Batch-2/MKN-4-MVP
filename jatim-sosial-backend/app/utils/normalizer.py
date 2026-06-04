def is_not_null(value) -> bool:
    return value is not None and str(value).strip() not in ("", "nan", "NaN", "None")

def safe_int(v, default=0):
    try:
        return int(float(v)) if v and str(v).strip() not in ("", "nan") else default
    except (ValueError, TypeError):
        return default

def fix_nik(v):
    """Konversi scientific notation '3.57301E+15' → '357301XXXXXXX'"""
    if not v:
        return None
    try:
        # Jika berupa scientific notation, konversi ke integer lalu string
        return str(int(float(v)))
    except (ValueError, TypeError):
        return str(v).strip()

def to_int(value, default=0):
    try:
        if not is_not_null(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
