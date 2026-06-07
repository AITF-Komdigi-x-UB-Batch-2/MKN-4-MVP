import httpx
import logging
import json
import asyncio
import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.config import AI_RUNPOD_URL, API_TIM_3_URL
from app.utils.enum import (
    HubKepalaEnum, StatusPerkawinanEnum, KondisiGiziEnum, PenyakitMenahunEnum,
    HambatanFungsiEnum, KesedihanDepresiEnum
)

logger = logging.getLogger(__name__)

def _hitung_umur(keluarga) -> int:
    """Hitung usia dari tanggal_lahir atau umur_2026."""
    if keluarga.umur_2026:
        return int(keluarga.umur_2026)
    if keluarga.tanggal_lahir:
        try:
            tahun = int(str(keluarga.tanggal_lahir).split("-")[0].strip())
            return datetime.datetime.now().year - tahun
        except Exception:
            pass
    return 0


def _hambatan_lbl(keluarga, field: str) -> str:
    val = getattr(keluarga, field, None)
    if val is None:
        return "Tidak mengalami kesulitan"
    return HambatanFungsiEnum.get_label(int(val), default="Tidak mengalami kesulitan")


def build_profil_warga(keluarga) -> str:
    """Rakit string profil_warga sesuai format yang diterima API Tim 3."""
    umur = _hitung_umur(keluarga)

    hub_kk  = HubKepalaEnum.get_label(keluarga.id_hub_kepala_keluarga, default="Kepala keluarga")
    st_kawin = StatusPerkawinanEnum.get_label(keluarga.id_status_perkawinan, default="Tidak diketahui")
    gizi     = KondisiGiziEnum.get_label(keluarga.id_kondisi_gizi, default="Tidak diketahui")
    penyakit = PenyakitMenahunEnum.get_label(keluarga.id_penyakit_menahun, default="Tidak diketahui")
    sedih    = KesedihanDepresiEnum.get_label(keluarga.id_kesedihan_depresi, default="Tidak diketahui")
    pbi_lbl  = "Ya" if keluarga.pbi == 1 else "Tidak"
    bansos   = keluarga.bansos or "Tidak ada"
    desil    = keluarga.desil_nasional or keluarga.desil_nasional_keluarga or "-"
    dtsen    = keluarga.status_dtsen or "DTSEN AKTIF"

    # Wilayah
    parts = [p for p in [
        keluarga.kelurahan_desa,
        f"Kec. {keluarga.kecamatan}" if keluarga.kecamatan else None,
        keluarga.kabupaten_kota,
        "Jawa Timur"
    ] if p]
    wilayah = ", ".join(parts) if parts else "Jawa Timur"

    return (
        f"- NIK / No. KK     : {keluarga.nik or '-'} / {keluarga.no_kk or '-'}\n"
        f"- Nama             : {keluarga.nama or keluarga.nama_kepala_keluarga or 'Tidak diketahui'}\n"
        f"- Umur             : {umur} tahun\n"
        f"- Hub. Kepala KK   : {hub_kk}\n"
        f"- Status Kawin     : {st_kawin}\n"
        f"- Jml. Anggota KK  : {keluarga.jumlah_anggota_keluarga or '-'} orang\n"
        f"- Desil Nasional   : {desil} | Status DTSEN: {dtsen}\n"
        f"- Bansos           : {bansos}\n"
        f"- PBI Jaminan Kes  : {pbi_lbl}\n"
        f"- Kondisi Gizi     : {gizi}\n"
        f"- Penyakit Menahun : {penyakit}\n"
        f"Hambatan Fungsi:\n"
        f"- Penglihatan      : {_hambatan_lbl(keluarga, 'id_penglihatan')} "
        f"| Pendengaran: {_hambatan_lbl(keluarga, 'id_pendengaran')}\n"
        f"- Berjalan/Tangga  : {_hambatan_lbl(keluarga, 'id_berjalan_atau_naik_tangga')} "
        f"| Tangan/Jari: {_hambatan_lbl(keluarga, 'id_menggunakan_tangan_jari')}\n"
        f"- Belajar/Intelek  : {_hambatan_lbl(keluarga, 'id_belajar_kemampuan_intelektual')} "
        f"| Perilaku: {_hambatan_lbl(keluarga, 'id_pengendalian_perilaku')}\n"
        f"- Bicara/Komunikasi: {_hambatan_lbl(keluarga, 'id_berbicara_komunikasi')} "
        f"| Mengurus Diri: {_hambatan_lbl(keluarga, 'id_mengurus_diri')}\n"
        f"- Ingatan/Fokus    : {_hambatan_lbl(keluarga, 'id_mengingat_berkonsentrasi')} "
        f"| Sedih/Depresi: {sedih}\n"
        f"- Wilayah          : {wilayah}"
    )


def get_role_and_user_content(keluarga, skor_pkh, skor_aspd):
    """Backward-compat wrapper — kembalikan (role_content, user_content)."""
    return "", build_profil_warga(keluarga)

def determine_eligibility(keluarga) -> list:
    """Fungsi pembantu untuk menyeleksi kelayakan program berdasarkan aturan Juknis Dinsos Jatim secara deterministik"""
    rekomendasi = []
    try:
        # 1. Hitung Umur
        umur = keluarga.umur_2026
        if umur is None and keluarga.tanggal_lahir:
            try:
                tahun_lahir_str = str(keluarga.tanggal_lahir).split("-")[0].strip()
                if tahun_lahir_str.isdigit():
                    tahun_lahir = int(tahun_lahir_str)
                    import datetime
                    tahun_sekarang = datetime.datetime.now().year
                    umur = tahun_sekarang - tahun_lahir
            except Exception:
                pass
        if umur is None:
            umur = 0
            
        # 2. Cek NIK Jawa Timur (BPS Code: 35)
        nik_str = str(keluarga.nik or "").strip()
        is_jatim = (
            nik_str.startswith("35") or
            (keluarga.provinsi and "JAWA TIMUR" in keluarga.provinsi.upper()) or
            (keluarga.kode_provinsi and str(keluarga.kode_provinsi).startswith("35"))
        )
        
        # 3. Cek Disabilitas
        has_disability = False
        if keluarga.id_disabilitas and keluarga.id_disabilitas > 0:
            has_disability = True
        if keluarga.tingkat_disabilitas and str(keluarga.tingkat_disabilitas).strip().upper() not in ("", "NONE", "0"):
            has_disability = True
        if keluarga.aspd == 1:
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
                    
        # 4. Evaluasi Kelayakan PKH Plus
        # Kriteria: (a) lansia >= 70 tahun, (b) desil 1-4, (c) NIK Jawa Timur
        desil = keluarga.desil_nasional
        pkh_plus_eligible = (umur >= 70) and (desil is not None and 1 <= desil <= 4) and is_jatim
        
        # 5. Evaluasi Kelayakan ASPD
        # Kriteria: (1) NIK Jawa Timur, (2) usia 6 bulan - 60 tahun (0.5 <= umur <= 60), (3) disabilitas/bed ridden
        aspd_eligible = is_jatim and (0.5 <= umur <= 60) and has_disability
        
        if pkh_plus_eligible:
            rekomendasi.append("PKH Plus")
        if aspd_eligible:
            rekomendasi.append("ASPD")
            
    except Exception as e:
        logger.error(f"Gagal menentukan kelayakan program: {e}")
        
    return rekomendasi

def extract_rekomendasi(hasil_final: dict, keluarga) -> list:
    """
    Parse rekomendasi dari output Tim 3.
    Format Tim 3: {"rekomendasi": [{"nama_program": "...", "status": "ELIGIBLE"}]}
    Fallback ke determine_eligibility jika Tim 3 tidak return rekomendasi.
    """
    rekomendasi = []
    for item in hasil_final.get("rekomendasi", []):
        if item.get("status") == "ELIGIBLE":
            nama = item.get("nama_program", "").upper()
            if "ASPD" in nama or "DISABILITAS" in nama:
                if "ASPD" not in rekomendasi:
                    rekomendasi.append("ASPD")
            elif "PKH" in nama:
                if "PKH Plus" not in rekomendasi:
                    rekomendasi.append("PKH Plus")
    # Fallback deterministik jika Tim 3 tidak return rekomendasi sama sekali
    if not rekomendasi:
        rekomendasi = determine_eligibility(keluarga)
    return rekomendasi

async def execute_asesmen_sosial_logic_async(keluarga_id: UUID, user_id: UUID, db: Session):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        print(f"[Asinkron] Keluarga {keluarga_id} tidak ditemukan.")
        return
    
    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()

    try:
        payload_llm = {
            "profil_warga": build_profil_warga(keluarga),
            "top_k": 5
        }
        headers_api = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # 1. Panggilan HTTP ke API Tim 3
        try:
            async with httpx.AsyncClient() as client:
                # Langsung tembak ke endpoint Tim 3 secara pasti
                url_target = f"{API_TIM_3_URL}/recommend"
                
                response = await client.post(
                    url_target,
                    headers=headers_api,
                    json=payload_llm, 
                    timeout=60.0
                )
                response.raise_for_status()
                hasil_mentah = response.json()
                
                # Fleksibilitas Ekstrak Balasan:
                # Tetap dipertahankan untuk berjaga-jaga apakah Tim 3 mengembalikan 
                # format raw OpenAI (choices) atau JSON yang sudah mereka rapikan.
                if isinstance(hasil_mentah, str):
                    string_json_ai = hasil_mentah.strip().strip("```json").strip("```").strip()
                    hasil_final = json.loads(string_json_ai)
                elif isinstance(hasil_mentah, dict) and "choices" in hasil_mentah:
                    string_json_ai = hasil_mentah["choices"][0]["message"]["content"]
                    string_json_ai = string_json_ai.strip().strip("```json").strip("```").strip()
                    hasil_final = json.loads(string_json_ai)
                else:
                    hasil_final = hasil_mentah.get("justifikasi_dokumen", hasil_mentah)
                    
        except Exception as e:
            import logging
            logging.error(f"[Asinkron] Gagal memanggil API Tim 3 (Sosial): {e}", exc_info=True)
            
            # --- FALLBACK DETERMINISTIK ---
            hasil_final = {
                "rekomendasi": determine_eligibility(keluarga),
                "ringkasan_profil": "Sistem menggunakan analisis cadangan (Fallback Deterministik) karena koneksi ke API AI Tim 3 terputus atau URL belum dikonfigurasi.",
                "rekomendasi_teknis_bansos": "Warga ini dievaluasi secara otomatis menggunakan sistem desil, usia lansia, dan filter disabilitas sesuai standar Juknis Jatim dasar tanpa analisis LLM."
            }

        # 3. Simpan Rekomendasi Program & Detail Analisis
        rekomendasi_baru = extract_rekomendasi(hasil_final, keluarga)

        # Reasoning: gabungkan ringkasan + rekomendasi teknis dari Tim 3
        ringkasan    = hasil_final.get("ringkasan_profil", "")
        teknis       = hasil_final.get("rekomendasi_teknis_bansos", "")
        analisis_rag = json.dumps(
            {"ringkasan_profil": ringkasan, "rekomendasi_teknis": teknis,
             "rekomendasi": hasil_final.get("rekomendasi", [])},
            ensure_ascii=False
        )

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=user_id)
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        hitung.status_validasi = "validasi" if len(rekomendasi_baru) > 0 else "ditolak"

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag
        # MENGHITUNG SKOR PADA SAAT ANALISIS BUKAN SAAT IMPOR
        from app.utils.scoring import hitung_skor_bantuan
        skor = hitung_skor_bantuan(keluarga)
        hitung.skor_pkh_plus = skor.get("skor_pkh_plus")
        hitung.skor_aspd = skor.get("skor_aspd")

        log = models.LogHistori(
            keluarga_id=keluarga.id,
            user_id=user_id,
            desil_lama=None,
            desil_baru=None,
            bantuan_lama=bantuan_lama,
            bantuan_baru=rekomendasi_baru
        )
        db.add(log)
        db.commit()
        print(f"[Asinkron] Asesmen sukses untuk KK {keluarga.no_kk}. Rekomendasi: {rekomendasi_baru}")
    
    except Exception as e:
        db.rollback()
        print(f"[Asinkron DB Error] {e}")
        # Try to reset status to 'validasi' to avoid getting stuck
        try:
            hitung_reset = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()
            if hitung_reset:
                hitung_reset.status_validasi = "validasi"
                db.commit()
        except Exception as db_ex:
            print(f"[Asinkron Failure Reset Error] {db_ex}")
