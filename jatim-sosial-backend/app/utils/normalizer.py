def is_not_null(value) -> bool:
    return value is not None and str(value).strip() not in ("", "nan", "NaN", "None")

def safe_int(v, default=0):
    if not v:
        return default
    v_str = str(v).strip().strip("[]").strip()
    if v_str in ("", "nan", "NaN", "None"):
        return default
    try:
        return int(float(v_str))
    except (ValueError, TypeError):
        return default

def fix_nik(v):
    """Konversi scientific notation '3.57301E+15' → '357301XXXXXXX'"""
    if not v:
        return None
    try:
        # Jika berupa scientific notation, konversi ke integer lalu string
        v_str = str(v).strip().strip("[]").strip()
        return str(int(float(v_str)))
    except (ValueError, TypeError):
        return str(v).strip()

def to_int(value, default=0):
    try:
        if not is_not_null(value):
            return default
        v_str = str(value).strip().strip("[]").strip()
        return int(float(v_str))
    except (TypeError, ValueError):
        return default
