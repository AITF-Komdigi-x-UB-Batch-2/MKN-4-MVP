from app.utils.normalizer import to_int
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

# ==========================================
# FUNGSI HELPER NORMALISASI SAW (Skala 0.0 - 1.0)
# ==========================================

PKH_PLUS_WEIGHTS = {
    "usia": 0.0847,
    "desil_nasional": 0.0847,
    "bansos": 0.0847,
    "jumlah_anggota_keluarga": 0.0678,
    "id_mengurus_diri": 0.0678,
    "pbi": 0.0508,
    "id_penglihatan": 0.0508,
    "id_pendengaran": 0.0508,
    "id_berjalan_atau_naik_tangga": 0.0508,
    "id_berbicara_komunikasi": 0.0508,
    "id_mengingat_berkonsentrasi": 0.0508,
    "id_penyakit_menahun": 0.0508,
    "id_status_penguasaan_bangunan": 0.0508,
    "id_lantai_terluas": 0.0508,
    "luas_lantai_bangunan": 0.0508,
    "id_dinding_terluas": 0.0508,
    "id_atap_terluas": 0.0508,
}

ASPD_WEIGHTS = {
    "id_kondisi_gizi": 0.10,
    "id_berjalan_atau_naik_tangga": 0.10,
    "id_mengurus_diri": 0.10,
    "desil_nasional": 0.10,
    "pbi": 0.08,
    "id_penglihatan": 0.06,
    "id_pendengaran": 0.06,
    "id_menggunakan_tangan_jari": 0.06,
    "id_belajar_kemampuan_intelektual": 0.06,
    "id_pengendalian_perilaku": 0.06,
    "id_berbicara_komunikasi": 0.06,
    "id_mengingat_berkonsentrasi": 0.06,
    "id_penyakit_menahun": 0.06,
    "jumlah_anggota_keluarga": 0.04,
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def saw_to_percent(score: float) -> float:
    return round(clamp(score) * 100.0, 2)

def normalisasi_hambatan(val) -> float:
    """
    1: Sama sekali tidak bisa (Sangat rentan) -> 1.0
    2: Banyak kesulitan dan membutuhkan bantuan -> 0.67
    3: Sedikit kesulitan -> 0.33
    4: Tidak mengalami kesulitan -> 0.0
    """
    val_int = to_int(val, 4)
    if val_int < 1 or val_int > 4:
        return 0.0
    return clamp((4 - val_int) / 3.0)

def normalisasi_desil(desil, max_desil: int) -> float:
    """Cost normalization: Desil paling rendah mendapat skor tertinggi."""
    d = to_int(desil, max_desil)
    if d < 1 or d > max_desil:
        return 0.0
    return clamp((max_desil - d) / float(max_desil - 1))

def normalisasi_usia_pkh(umur) -> float:
    """Benefit min-max dengan batas bawah Juknis PKH Plus 70 tahun."""
    u = to_int(umur, 0)
    if u < 70:
        return 0.0

    # Batas atas praktis agar skor tetap stabil untuk data satu baris.
    return clamp((u - 70) / 30.0)

def normalisasi_jumlah_anggota(jml) -> float:
    """Maksimal referensi keluarga 10 orang untuk pembagi skala 0-1"""
    j = to_int(jml, 1)
    return clamp((j - 1) / 9.0)

def cek_penyakit_menahun(val) -> float:
    """1 = Tidak ada (0.0). > 1 = Ada penyakit (1.0)"""
    v = to_int(val, 1)
    return 1.0 if v > 1 else 0.0


def normalisasi_status_bangunan(val) -> float:
    """
    C13 - 1: Milik sendiri (0.00), 4: Dinas (0.33), 3: Bebas sewa / 5: Lainnya (0.67), 2: Kontrak/sewa (1.00)
    """
    v = to_int(val, 1)
    if v == 1:
        return 0.00
    if v == 4:
        return 0.33
    if v in [3, 5]:
        return 0.67
    if v == 2:
        return 1.00
    return 0.67

def normalisasi_lantai(val) -> float:
    """
    C14 - 1,2,3: Marmer/Granit/Keramik/Parket/Vinyl/Karpet (0.00)
          4: Ubin/Tegel/Teraso (0.33)
          5,6,9: Kayu/Papan/Semen/Bata Merah/Lainnya (0.67)
          7,8: Bambu/Tanah (1.00)
    """
    v = to_int(val, 1)
    if v in [1, 2, 3]:
        return 0.00
    if v == 4:
        return 0.33
    if v in [5, 6, 9]:
        return 0.67
    if v in [7, 8]:
        return 1.00
    return 0.67

def normalisasi_dinding(val) -> float:
    """
    C16 - 1: Tembok (0.00)
          2: Plesteran Anyaman Bambu/Kawat (0.33)
          3,7: Kayu/Papan/Gypsum/GRC/Calciboard/Lainnya (0.67)
          4,5,6: Anyaman Bambu/Batang Kayu/Bambu (1.00)
    """
    v = to_int(val, 1)
    if v == 1:
        return 0.00
    if v == 2:
        return 0.33
    if v in [3, 7]:
        return 0.67
    if v in [4, 5, 6]:
        return 1.00
    return 0.67

def normalisasi_atap(val) -> float:
    """
    C17 - 1: Beton (0.00)
          2: Genteng (0.33)
          3,4,5,6: Seng/Asbes/Bambu/Kayu/Sirap (0.67)
          7,8: Jerami/Ijuk/Daun-daunan/Rumbia/Lainnya (1.00)
    """
    v = to_int(val, 1)
    if v == 1:
        return 0.00
    if v == 2:
        return 0.33
    if v in [3, 4, 5, 6]:
        return 0.67
    if v in [7, 8]:
        return 1.00
    return 0.67

def normalisasi_luas_per_kapita(luas_lantai, jumlah_anggota) -> float:
    luas = float(luas_lantai or 0.0)
    anggota = max(1, to_int(jumlah_anggota, 1))
    return 1.0 if (luas / anggota) < 7.2 else 0.0

def normalisasi_gizi(val) -> float:
    """
    C1 (ASPD) - 1: Kurang gizi/Wasting (1.0), 2: Kerdil/Stunting (0.5), 3 atau 8: Tidak ada/Tidak tahu (0.0)
    """
    v = to_int(val, 3)
    if v == 1:
        return 1.0
    if v == 2:
        return 0.5
    return 0.0

def normalisasi_desil_aspd(val) -> float:
    """
    C4 (ASPD) - 1: Desil 1 (1.00), 2: Desil 2 (0.75), 3: Desil 3 (0.50), 4: Desil 4 (0.25), 5: Desil 5 (0.00)
    """
    v = to_int(val, 5)
    mapping = {1: 1.00, 2: 0.75, 3: 0.50, 4: 0.25, 5: 0.00}
    return mapping.get(v, 0.00)

def parse_umur(keluarga) -> int:
    umur = getattr(keluarga, "umur_2026", None)
    if umur is not None:
        try:
            return to_int(umur, 0)
        except Exception:
            pass

    tanggal_lahir = getattr(keluarga, "tanggal_lahir", None)
    if not tanggal_lahir:
        return 0

    val_str = str(tanggal_lahir).strip()
    if not val_str:
        return 0

    # Cek jika hanya tahun saja (4 digit angka)
    if val_str.isdigit() and len(val_str) == 4:
        try:
            return date.today().year - int(val_str)
        except Exception:
            pass

    # Coba format split untuk mengambil tahun pertama jika ada tanda hubung/slash
    for delimiter in ("-", "/", "."):
        if delimiter in val_str:
            parts = val_str.split(delimiter)
            # Biasanya YYYY-MM-DD
            if len(parts) >= 1 and len(parts[0]) == 4 and parts[0].isdigit():
                try:
                    return date.today().year - int(parts[0])
                except Exception:
                    pass
            # Atau DD-MM-YYYY
            if len(parts) >= 3 and len(parts[2]) == 4 and parts[2].isdigit():
                try:
                    return date.today().year - int(parts[2])
                except Exception:
                    pass

    # Fallback ke format standar datetime parse
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            lahir = datetime.strptime(val_str, fmt).date()
            today = date.today()
            return today.year - lahir.year - ((today.month, today.day) < (lahir.month, lahir.day))
        except ValueError:
            continue
    return 0


def get_desil(keluarga) -> int:
    for field in ("desil_nasional_anggota", "desil_nasional_keluarga", "desil_nasional"):
        value = getattr(keluarga, field, None)
        if value is not None:
            desil = to_int(value, 0)
            if desil > 0:
                return desil
    return 10


def is_dtsen_aktif(keluarga) -> bool:
    status = str(getattr(keluarga, "status_dtsen", "") or "").strip().lower()
    return not status or status in {"aktif", "active", "1", "true", "ya", "dtsen aktif"}


def is_jatim_identity(keluarga) -> bool:
    kode_provinsi = str(getattr(keluarga, "kode_provinsi", "") or "")
    nik = str(getattr(keluarga, "nik", "") or "")
    no_kk = str(getattr(keluarga, "no_kk", "") or "")
    provinsi = str(getattr(keluarga, "provinsi", "") or "").lower()

    # Beberapa dataset uji tidak mengisi field wilayah. Jika semua penanda
    # identitas kosong, jangan otomatis menggugurkan kandidat dari skoring.
    if not any([kode_provinsi, nik, no_kk, provinsi]):
        return True

    return (
        kode_provinsi in {"35", "3500"}
        or nik.startswith("35")
        or no_kk.startswith("35")
        or "jawa timur" in provinsi
    )


def is_pkh(keluarga) -> bool:
    bansos = str(getattr(keluarga, "bansos", "") or "").upper()
    pkh_plus = to_int(getattr(keluarga, "pkh_plus", 0), 0)
    return "PKH" in bansos or pkh_plus == 1


def eligible_pkh_plus(keluarga, umur: int, desil: int) -> bool:
    return (
        umur >= 70
        and is_pkh(keluarga)
        and is_dtsen_aktif(keluarga)
        and 1 <= desil <= 4
        and is_jatim_identity(keluarga)
    )


def eligible_aspd(keluarga, umur: int, desil: int) -> bool:
    if not (0 <= umur <= 60):
        return False
    if not is_jatim_identity(keluarga):
        return False
    if not is_dtsen_aktif(keluarga):
        return False
    if not (1 <= desil <= 5):
        return False
        
    has_disability = False
    if to_int(getattr(keluarga, "id_disabilitas", 0), 0) > 0:
        has_disability = True
    if getattr(keluarga, "tingkat_disabilitas", None) and str(keluarga.tingkat_disabilitas).strip().upper() not in ("", "NONE", "0"):
        has_disability = True
    if to_int(getattr(keluarga, "aspd", 0), 0) == 1:
        has_disability = True
        
    kolom_disabilitas = [
        "id_penglihatan", "id_pendengaran", "id_berjalan_atau_naik_tangga",
        "id_menggunakan_tangan_jari", "id_belajar_kemampuan_intelektual",
        "id_pengendalian_perilaku", "id_berbicara_komunikasi",
        "id_mengurus_diri", "id_mengingat_berkonsentrasi", "id_kesedihan_depresi"
    ]
    for col in kolom_disabilitas:
        val = getattr(keluarga, col, None)
        if val is not None:
            try:
                val_int = int(float(val))
                if 1 <= val_int <= 3:
                    has_disability = True
            except (ValueError, TypeError):
                pass
                
    return has_disability


# ==========================================
# VALIDASI BISNIS: PKH+ MAKS 1 PER KK
# ==========================================

def cek_kuota_pkh_plus_per_kk(no_kk: str, current_nik: str, db) -> bool:
    """
    Cek apakah KK ini sudah memiliki anggota lain yang eligible PKH+.
    Jika sudah ada 1 orang (dengan NIK berbeda), maka return False (ditolak).

    Parameter:
        no_kk: Nomor KK yang sedang diproses
        current_nik: NIK individu yang sedang dievaluasi
        db: SQLAlchemy Session

    Return: True jika masih boleh mendapat PKH+, False jika kuota sudah penuh.
    """
    from app import models

    existing_pkh = db.query(models.Keluarga).filter(
        models.Keluarga.no_kk == no_kk,
        models.Keluarga.nik != current_nik,
        models.Keluarga.status_bantuan.in_(["Eligible PKH+", "Eligible Keduanya"])
    ).first()

    if existing_pkh:
        logger.info(
            f"[KUOTA PKH+] KK {no_kk}: NIK {current_nik} DITOLAK. "
            f"Sudah ada penerima PKH+ di KK ini: NIK {existing_pkh.nik}"
        )
        return False
    return True


# ==========================================
# FUNGSI SKORING TERPISAH: PKH+ DAN ASPD
# ==========================================

def hitung_skor_pkh_plus(keluarga) -> dict:
    """
    Hitung skor PKH Plus secara mandiri.
    Return: {"eligible": bool, "skor": float (0-100)}
    """
    try:
        umur = parse_umur(keluarga)
        desil = get_desil(keluarga)
        is_eligible = eligible_pkh_plus(keluarga, umur, desil)

        if not is_eligible:
            return {"eligible": False, "skor": 0.0}

        pbi_val = 1.0 if to_int(getattr(keluarga, "pbi", 0), 0) == 1 else 0.0
        punya_pkh = 1.0 if is_pkh(keluarga) else 0.0
        jml_anggota = to_int(getattr(keluarga, "jumlah_anggota_keluarga", 1), 1)

        skor_raw = (
            normalisasi_usia_pkh(umur) * PKH_PLUS_WEIGHTS["usia"]
            + normalisasi_desil(desil, 4) * PKH_PLUS_WEIGHTS["desil_nasional"]
            + punya_pkh * PKH_PLUS_WEIGHTS["bansos"]
            + normalisasi_hambatan(getattr(keluarga, "id_mengurus_diri", 4)) * PKH_PLUS_WEIGHTS["id_mengurus_diri"]
            + normalisasi_jumlah_anggota(jml_anggota) * PKH_PLUS_WEIGHTS["jumlah_anggota_keluarga"]
            + pbi_val * PKH_PLUS_WEIGHTS["pbi"]
            + normalisasi_hambatan(getattr(keluarga, "id_penglihatan", 4)) * PKH_PLUS_WEIGHTS["id_penglihatan"]
            + normalisasi_hambatan(getattr(keluarga, "id_pendengaran", 4)) * PKH_PLUS_WEIGHTS["id_pendengaran"]
            + normalisasi_hambatan(getattr(keluarga, "id_berjalan_atau_naik_tangga", 4)) * PKH_PLUS_WEIGHTS["id_berjalan_atau_naik_tangga"]
            + normalisasi_hambatan(getattr(keluarga, "id_berbicara_komunikasi", 4)) * PKH_PLUS_WEIGHTS["id_berbicara_komunikasi"]
            + normalisasi_hambatan(getattr(keluarga, "id_mengingat_berkonsentrasi", 4)) * PKH_PLUS_WEIGHTS["id_mengingat_berkonsentrasi"]
            + cek_penyakit_menahun(getattr(keluarga, "id_penyakit_menahun", 1)) * PKH_PLUS_WEIGHTS["id_penyakit_menahun"]
            + normalisasi_status_bangunan(getattr(keluarga, "id_status_penguasaan_bangunan", 1)) * PKH_PLUS_WEIGHTS["id_status_penguasaan_bangunan"]
            + normalisasi_lantai(getattr(keluarga, "id_lantai_terluas", 1)) * PKH_PLUS_WEIGHTS["id_lantai_terluas"]
            + normalisasi_luas_per_kapita(getattr(keluarga, "luas_lantai_bangunan", 0), jml_anggota) * PKH_PLUS_WEIGHTS["luas_lantai_bangunan"]
            + normalisasi_dinding(getattr(keluarga, "id_dinding_terluas", 1)) * PKH_PLUS_WEIGHTS["id_dinding_terluas"]
            + normalisasi_atap(getattr(keluarga, "id_atap_terluas", 1)) * PKH_PLUS_WEIGHTS["id_atap_terluas"]
        )

        skor_final = saw_to_percent(skor_raw)
        logger.info(f"[SCORING PKH+] NIK: {keluarga.nik}, Skor: {skor_final}%")
        return {"eligible": True, "skor": skor_final}

    except Exception as e:
        logger.error(f"Gagal menghitung skor PKH+: {e}", exc_info=True)
        return {"eligible": False, "skor": 0.0}


def hitung_skor_aspd(keluarga) -> dict:
    """
    Hitung skor ASPD secara mandiri.
    Return: {"eligible": bool, "skor": float (0-100)}
    """
    try:
        umur = parse_umur(keluarga)
        desil = get_desil(keluarga)
        is_eligible = eligible_aspd(keluarga, umur, desil)

        if not is_eligible:
            return {"eligible": False, "skor": 0.0}

        pbi_val = 1.0 if to_int(getattr(keluarga, "pbi", 0), 0) == 1 else 0.0
        jml_anggota = to_int(getattr(keluarga, "jumlah_anggota_keluarga", 1), 1)

        skor_raw = (
            normalisasi_gizi(getattr(keluarga, "id_kondisi_gizi", 3)) * ASPD_WEIGHTS["id_kondisi_gizi"]
            + normalisasi_hambatan(getattr(keluarga, "id_berjalan_atau_naik_tangga", 4)) * ASPD_WEIGHTS["id_berjalan_atau_naik_tangga"]
            + normalisasi_hambatan(getattr(keluarga, "id_mengurus_diri", 4)) * ASPD_WEIGHTS["id_mengurus_diri"]
            + normalisasi_desil_aspd(desil) * ASPD_WEIGHTS["desil_nasional"] # <--- UBAH BARIS INI
            + pbi_val * ASPD_WEIGHTS["pbi"]
            + normalisasi_hambatan(getattr(keluarga, "id_penglihatan", 4)) * ASPD_WEIGHTS["id_penglihatan"]
            + normalisasi_hambatan(getattr(keluarga, "id_pendengaran", 4)) * ASPD_WEIGHTS["id_pendengaran"]
            + normalisasi_hambatan(getattr(keluarga, "id_menggunakan_tangan_jari", 4)) * ASPD_WEIGHTS["id_menggunakan_tangan_jari"]
            + normalisasi_hambatan(getattr(keluarga, "id_belajar_kemampuan_intelektual", 4)) * ASPD_WEIGHTS["id_belajar_kemampuan_intelektual"]
            + normalisasi_hambatan(getattr(keluarga, "id_pengendalian_perilaku", 4)) * ASPD_WEIGHTS["id_pengendalian_perilaku"]
            + normalisasi_hambatan(getattr(keluarga, "id_berbicara_komunikasi", 4)) * ASPD_WEIGHTS["id_berbicara_komunikasi"]
            + normalisasi_hambatan(getattr(keluarga, "id_mengingat_berkonsentrasi", 4)) * ASPD_WEIGHTS["id_mengingat_berkonsentrasi"]
            + cek_penyakit_menahun(getattr(keluarga, "id_penyakit_menahun", 1)) * ASPD_WEIGHTS["id_penyakit_menahun"]
            + normalisasi_jumlah_anggota(jml_anggota) * ASPD_WEIGHTS["jumlah_anggota_keluarga"]
        )

        skor_final = saw_to_percent(skor_raw)
        logger.info(f"[SCORING ASPD] NIK: {keluarga.nik}, Skor: {skor_final}%")
        return {"eligible": True, "skor": skor_final}

    except Exception as e:
        logger.error(f"Gagal menghitung skor ASPD: {e}", exc_info=True)
        return {"eligible": False, "skor": 0.0}


def hitung_skor_bantuan(keluarga) -> dict: 
    """
    Wrapper backward-compatible. Memanggil fungsi terpisah PKH+ dan ASPD.
    Menerima parameter 'keluarga' (Object SQLAlchemy models.Keluarga).

    Return: {"skor_pkh_plus": float, "skor_aspd": float,
             "eligible_pkh_plus": bool, "eligible_aspd": bool}
    """
    hasil_pkh = hitung_skor_pkh_plus(keluarga)
    hasil_aspd = hitung_skor_aspd(keluarga)

    logger.info(
        f"[SCORING] NIK: {keluarga.nik}, KK: {keluarga.no_kk}. "
        f"PKH+ eligible={hasil_pkh['eligible']} skor={hasil_pkh['skor']}%, "
        f"ASPD eligible={hasil_aspd['eligible']} skor={hasil_aspd['skor']}%"
    )

    return {
        "skor_pkh_plus": hasil_pkh["skor"],
        "skor_aspd": hasil_aspd["skor"],
        "eligible_pkh_plus": hasil_pkh["eligible"],
        "eligible_aspd": hasil_aspd["eligible"],
    }

