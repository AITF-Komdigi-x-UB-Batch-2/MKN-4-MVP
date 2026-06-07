from app.utils.normalizer import to_int
import logging

logger = logging.getLogger(__name__)

# ==========================================
# FUNGSI HELPER NORMALISASI (Skala 0.0 - 1.0)
# ==========================================

def normalisasi_hambatan(val) -> float:
    """
    1: Sama sekali tidak bisa (Sangat rentan) -> 1.0
    2: Banyak kesulitan -> 0.5
    3: Sedikit/Tidak ada kesulitan -> 0.0
    """
    val_int = to_int(val, 3)
    if val_int == 1: return 1.0
    elif val_int == 2: return 0.5
    else: return 0.0

def normalisasi_desil(desil) -> float:
    """Desil 1 (Miskin) -> 1.0, Desil 10 (Kaya) -> 0.1"""
    d = to_int(desil, 10)
    return max(0.0, (11 - d) / 10.0)

def normalisasi_umur(umur) -> float:
    """Umur >= 70 langsung dapat 1.0 (Prioritas PKH Plus Lanjut Usia)"""
    u = to_int(umur, 0)
    if u >= 70: return 1.0
    return min(1.0, u / 70.0)

def normalisasi_jumlah_anggota(jml) -> float:
    """Maksimal referensi keluarga 10 orang untuk pembagi skala 0-1"""
    j = to_int(jml, 1)
    return min(1.0, float(j) / 10.0)

def cek_penyakit_menahun(val) -> float:
    """1 = Tidak ada (0.0). > 1 = Ada penyakit (1.0)"""
    v = to_int(val, 1)
    return 1.0 if v > 1 else 0.0


# ==========================================
# FUNGSI SKORING UTAMA UNTUK OBJECT SQLALCHEMY
# ==========================================

def hitung_skor_bantuan(keluarga) -> dict:
    """
    Menghitung skor probabilitas kelayakan PKH Plus dan ASPD berdasarkan Juknis.
    Menerima parameter 'keluarga' (Object SQLAlchemy models.Keluarga).
    """
    try:
        # --- EKSTRAK DATA DASAR ---
        # Menggunakan umur_2026 sesuai database
        umur = to_int(getattr(keluarga, "umur_2026", 0), 0)
        desil = to_int(getattr(keluarga, "desil_nasional", 10), 10)
        
        # PBI di database Integer (asumsi 1 = Ya, 0 = Tidak)
        pbi_val = 1.0 if to_int(getattr(keluarga, "pbi", 0), 0) == 1 else 0.0
        
        bansos_str = str(getattr(keluarga, "bansos", "")).upper()
        punya_pkh = 1.0 if 'PKH' in bansos_str else 0.0
        
        jml_anggota = to_int(getattr(keluarga, "jumlah_anggota_keluarga", 1), 1)
        luas_lantai = float(getattr(keluarga, "luas_lantai_bangunan", 100.0) or 100.0)
        luas_per_kapita = luas_lantai / jml_anggota if jml_anggota > 0 else luas_lantai

        # --- NORMALISASI INFRASTRUKTUR HUNIAN ---
        id_bangunan = to_int(getattr(keluarga, "id_status_penguasaan_bangunan", 1), 1)
        skor_bangunan = 0.0 if id_bangunan in [1, 4] else (0.5 if id_bangunan == 2 else 1.0)

        id_lantai = to_int(getattr(keluarga, "id_lantai_terluas", 1), 1)
        skor_lantai = 0.0 if id_lantai in [1, 2, 3] else (0.5 if id_lantai in [4, 5, 6] else 1.0)

        id_dinding = to_int(getattr(keluarga, "id_dinding_terluas", 1), 1)
        skor_dinding = 0.0 if id_dinding == 1 else (0.5 if id_dinding in [2, 3] else 1.0)

        id_atap = to_int(getattr(keluarga, "id_atap_terluas", 1), 1)
        skor_atap = 0.0 if id_atap in [1, 2] else (0.5 if id_atap in [3, 4] else 1.0)

        skor_luas_kapita = 1.0 if luas_per_kapita < 7.2 else 0.0

        # --- NORMALISASI KONDISI GIZI ---
        id_gizi = to_int(getattr(keluarga, "id_kondisi_gizi", 3), 3)
        skor_gizi = 1.0 if id_gizi in [1, 2] else 0.0

        # ==========================================
        # 1. PERHITUNGAN PKH PLUS (Total Bobot: 59)
        # ==========================================
        skor_pkh = 0.0
        
        skor_pkh += normalisasi_umur(umur) * 5.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_mengurus_diri', 3)) * 4.0
        skor_pkh += pbi_val * 3.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_penglihatan', 3)) * 3.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_pendengaran', 3)) * 3.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_berjalan_atau_naik_tangga', 3)) * 3.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_berbicara_komunikasi', 3)) * 3.0
        skor_pkh += normalisasi_hambatan(getattr(keluarga, 'id_mengingat_berkonsentrasi', 3)) * 3.0
        skor_pkh += cek_penyakit_menahun(getattr(keluarga, 'id_penyakit_menahun', 1)) * 3.0
        
        skor_pkh += normalisasi_desil(desil) * 5.0
        skor_pkh += punya_pkh * 5.0
        skor_pkh += normalisasi_jumlah_anggota(jml_anggota) * 4.0
        skor_pkh += skor_bangunan * 3.0
        skor_pkh += skor_lantai * 3.0
        skor_pkh += skor_luas_kapita * 3.0
        skor_pkh += skor_dinding * 3.0
        skor_pkh += skor_atap * 3.0

        # ==========================================
        # 2. PERHITUNGAN ASPD (Total Bobot: 50)
        # ==========================================
        skor_aspd = 0.0
        
        skor_aspd += skor_gizi * 5.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_berjalan_atau_naik_tangga', 3)) * 5.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_mengurus_diri', 3)) * 5.0
        skor_aspd += pbi_val * 4.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_penglihatan', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_pendengaran', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_menggunakan_tangan_jari', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_belajar_kemampuan_intelektual', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_pengendalian_perilaku', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_berbicara_komunikasi', 3)) * 3.0
        skor_aspd += normalisasi_hambatan(getattr(keluarga, 'id_mengingat_berkonsentrasi', 3)) * 3.0
        skor_aspd += cek_penyakit_menahun(getattr(keluarga, 'id_penyakit_menahun', 1)) * 3.0
        
        skor_aspd += normalisasi_desil(desil) * 5.0
        skor_aspd += normalisasi_jumlah_anggota(jml_anggota) * 2.0

        # ==========================================
        # 3. KONVERSI PERSENTASE MAKSIMAL 100
        # ==========================================
        persentase_pkh = round((skor_pkh / 59.0) * 100, 2)
        persentase_aspd = round((skor_aspd / 50.0) * 100, 2)

        return {
            "skor_pkh_plus": max(0.0, min(100.0, persentase_pkh)),
            "skor_aspd": max(0.0, min(100.0, persentase_aspd))
        }

    except Exception as e:
        logger.error(f"Gagal menghitung skor bansos: {e}", exc_info=True)
        return {"skor_pkh_plus": 0.0, "skor_aspd": 0.0}