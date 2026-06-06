import httpx
import logging
import json
import asyncio
from uuid import UUID
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.config import AI_RUNPOD_URL, AI_RUNPOD_TOKEN

logger = logging.getLogger(__name__)

async def mock_qdrant_retriever(query_text: str) -> str:
    """
    Simulasi pemanggilan database vektor Qdrant milik Tim 3.
    """
    return """
    [Konteks Kebijakan Sosial Jawa Timur]
    - PKH Plus: (a) lansia >= 70 tahun, (b) desil 1-4 DTSEN, (c) memiliki NIK Jawa Timur.
    - ASPD: (1) NIK Jawa Timur, (2) usia 6 bulan - 60 tahun, (3) penyandang disabilitas/bed ridden, (4) prioritas desil 1-5.
    """

def get_role_and_user_content(keluarga, skor_pkh, skor_aspd, konteks_aturan):
    """
    Fungsi bantuan untuk merakit prompt agar tidak ada kode yang diulang (DRY).
    """
    role_content = (
        "Anda adalah AI Auditor resmi Dinas Sosial Provinsi Jawa Timur yang bertugas melakukan verifikasi dan validasi kelayakan penerima manfaat dua program bantuan sosial:\n"
        "1. PKH Plus — Program Keluarga Harapan Plus, menyasar keluarga dengan kerentanan sosial-ekonomi berlapis (kemiskinan ekstrem, hunian tidak layak, masalah gizi, dan penyakit menahun).\n"
        "2. ASPD — Asistensi Sosial Penyandang Disabilitas, menyasar individu dengan hambatan fungsi fisik/mental signifikan yang mengurangi kemandirian dan kapasitas ekonomi.\n\n"
        "TUGAS ANDA:\n"
        "Untuk setiap profil warga, susun laporan evaluasi kelayakan yang sistematis dan dapat dipertanggungjawabkan secara administratif sesuai standar Kementerian Sosial RI.\n\n"
        "KERANGKA ANALISIS WAJIB (jalankan berurutan):\n"
        "1. PROFIL WARGA — Identifikasi identitas, posisi dalam keluarga, dan konteks sosial dasar.\n"
        "2. DEMOGRAFI — Nilai kelompok usia, status perkawinan, jumlah tanggungan, dan risiko sosial yang melekat.\n"
        "3. EKONOMI — Interpretasikan desil nasional: 1-2=miskin ekstrem, 3-4=rentan, 5-6=hampir miskin, 7-10=tidak miskin.\n"
        "4. INFRASTRUKTUR & HUNIAN — Nilai penguasaan bangunan dan luas lantai terhadap standar 36 m2 keluarga inti.\n"
        "5. KESEHATAN & GIZI — Evaluasi kondisi gizi dan penyakit menahun sebagai proxy beban ekonomi kesehatan.\n"
        "6. DISABILITAS & FUNGSI — Nilai 10 dimensi fungsi (penglihatan, pendengaran, mobilitas, tangan/jari, intelektual, perilaku, komunikasi, perawatan diri, memori/konsentrasi, kesedihan/depresi). Hambatan berat/total pada 1+ dimensi adalah indikator utama ASPD.\n"
        "7. SINTESIS — Agregasikan temuan, identifikasi co-occurring deprivation, dan berikan justifikasi LAYAK/TIDAK LAYAK untuk masing-masing program secara terpisah berdasarkan kriteria resmi berikut:\n"
        "   PKH Plus: (a) lansia >= 70 tahun, (b) desil 1-4 DTSEN, (c) memiliki NIK Jawa Timur.\n"
        "   ASPD: (1) NIK Jawa Timur, (2) usia 6 bulan - 60 tahun, (3) penyandang disabilitas/bed ridden, (4) prioritas desil 1-5; desil 6-10 wajib verifikasi lapangan.\n\n"
        "FORMAT OUTPUT:\n"
        "Seluruh respons WAJIB berupa satu objek JSON valid tanpa teks tambahan, tanpa markdown, tanpa komentar. Ikuti skema 'laporan_evaluasi' yang mencakup: profil_warga, analisis (per dimensi), skor, dan kesimpulan (untuk pkh_plus dan aspd masing-masing dengan status_kelayakan, urgensi, dan label)."
    )

    # Hitung umur secara dinamis dari tanggal_lahir
    umur = 0
    if keluarga.tanggal_lahir:
        try:
            tahun_lahir_str = str(keluarga.tanggal_lahir).split("-")[0].strip()
            if tahun_lahir_str.isdigit():
                tahun_lahir = int(tahun_lahir_str)
                import datetime
                tahun_sekarang = datetime.datetime.now().year
                umur = tahun_sekarang - tahun_lahir
        except Exception:
            pass

    user_content = f"""Profil Warga:
- NIK              : {keluarga.nik or 'Tidak diketahui'}
- Nama             : {keluarga.nama_kepala_keluarga}
- Umur             : {umur} tahun
- Hub. Kepala KK   : {getattr(keluarga, 'id_hub_kepala_keluarga', 'Kepala Keluarga')}
- Status Perkawinan: {getattr(keluarga, 'id_status_perkawinan', 'Tidak diketahui')}
- Desil Nasional   : {keluarga.desil_nasional}
- Jml. Anggota KK  : {keluarga.jumlah_anggota_keluarga} orang
- Penguasaan Bgn.  : {getattr(keluarga, 'id_status_penguasaan_bangunan', 'Milik Sendiri')}
- Luas Bangunan    : {getattr(keluarga, 'luas_lantai_bangunan', 0.0)} m2
- Kondisi Gizi     : Tidak diketahui
- Penyakit Menahun : Tidak diketahui
- Penglihatan      : {keluarga.id_penglihatan or 'Tidak mengalami kesulitan'}
- Pendengaran      : {getattr(keluarga, 'id_pendengaran', 'Tidak mengalami kesulitan')}
- Berjalan/Tangga  : {keluarga.id_berjalan_atau_naik_tangga or 'Tidak mengalami kesulitan'}
- Tangan/Jari      : {getattr(keluarga, 'id_menggunakan_tangan_jari', 'Tidak mengalami kesulitan')}
- Belajar/Intelektual: {getattr(keluarga, 'id_belajar_kemampuan_intelektual', 'Tidak mengalami kesulitan')}
- Pengendalian Perilaku: {getattr(keluarga, 'id_pengendalian_perilaku', 'Tidak mengalami kesulitan')}
- Bicara/Komunikasi: {getattr(keluarga, 'id_berbicara_komunikasi', 'Tidak mengalami kesulitan')}
- Mengurus Diri    : {getattr(keluarga, 'id_mengurus_diri', 'Tidak mengalami kesulitan')}
- Memori/Konsentrasi: {getattr(keluarga, 'id_mengingat_berkonsentrasi', 'Tidak mengalami kesulitan')}
- Kesedihan/Depresi: {getattr(keluarga, 'id_kesedihan_depresi', 'Tidak mengalami kesulitan')}
- Status DTSEN     : DTSEN AKTIF
- Wilayah          : Jawa Timur
- Izin Usaha       : Tidak diketahui
- Jml. Jenis Usaha : 0
- Omset Usaha Utama: Tidak diketahui

Skor Prioritas Bantuan (semakin mendekati 100 = semakin prioritas):
- Skor PKH Plus    : {skor_pkh}
- Skor ASPD        : {skor_aspd}

Tolong buatkan laporan evaluasi kelayakan untuk program PKH Plus dan ASPD.
Kamu harus merujuk pada aturan berikut sebagai konteks kebijakan:
<hasil_retrieval>
{konteks_aturan}
</hasil_retrieval>
"""
    return role_content, user_content

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
    """Fungsi aman untuk mengekstrak array rekomendasi bantuan dari format JSON Tim 3 dengan validasi aturan seleksi ketat (deterministic selector)"""
    return determine_eligibility(keluarga)

async def execute_asesmen_sosial_logic_async(keluarga_id: UUID, user_id: UUID, db: Session):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        print(f"[Asinkron] Keluarga {keluarga_id} tidak ditemukan.")
        return
    
    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    skor_pkh = hitung.skor_pkh_plus if hitung and hitung.skor_pkh_plus else 0.0
    skor_aspd = hitung.skor_aspd if hitung and hitung.skor_aspd else 0.0

    try:
        konteks_aturan = await mock_qdrant_retriever("syarat penerima bansos")
        role_content, user_content = get_role_and_user_content(keluarga, skor_pkh, skor_aspd, konteks_aturan)

        # Payload Model Baru (Runpod/OpenAI)
        payload_llm = {
            "model": "aitf-ub-2026/cpt-qwen3-8b-sft_v1",
            "messages": [
                {"role": "system", "content": role_content},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        headers_runpod = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_RUNPOD_TOKEN}"
        }

        # 1. Panggilan HTTP ke RunPod
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    AI_RUNPOD_URL,
                    headers=headers_runpod,
                    json=payload_llm,
                    timeout=60.0
                )
                response.raise_for_status()
                hasil_mentah = response.json()
        except httpx.HTTPError as he:
            logger.error(f"[Asinkron Runpod HTTP Error] Gagal melakukan request ke Runpod: {he}", exc_info=True)
            if hitung:
                hitung.status_validasi = "analisis"
                db.commit()
            return

        # 2. Parsing Output Tim 3
        try:
            choices = hasil_mentah.get("choices", [])
            if not choices:
                raise ValueError("JSON Runpod tidak memiliki field 'choices'")
            
            raw_text = choices[0]["message"]["content"]
            hasil_final = json.loads(raw_text)
        except Exception as pe:
            logger.error(f"[Asinkron Parse Error] Gagal parsing output AI JSON: {pe}. Output Mentah: {hasil_mentah}", exc_info=True)
            if hitung:
                hitung.status_validasi = "analisis"
                db.commit()
            return

        # 3. Simpan Rekomendasi Program & Detail Analisis
        rekomendasi_baru = extract_rekomendasi(hasil_final, keluarga)
        
        try:
            analisis_rag = hasil_final.get("laporan_evaluasi", {}).get("analisis", {})
            analisis_rag = json.dumps(analisis_rag, ensure_ascii=False)
        except Exception:
            analisis_rag = "{}"

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=user_id)
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag
        
        # Ekstrak skor dari respon AI jika ada
        skor_obj = hasil_final.get("skor", {})
        skor_aspd_ai = skor_obj.get("skor_aspd")
        skor_pkh_ai = skor_obj.get("skor_pkh_plus")
        if skor_aspd_ai is not None:
            hitung.skor_aspd = float(skor_aspd_ai)
        if skor_pkh_ai is not None:
            hitung.skor_pkh_plus = float(skor_pkh_ai)

        hitung.status_validasi = "analisis"

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
        # Try to reset status to 'analisis' to avoid getting stuck
        try:
            hitung_reset = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()
            if hitung_reset:
                hitung_reset.status_validasi = "analisis"
                db.commit()
        except Exception as db_ex:
            print(f"[Asinkron Failure Reset Error] {db_ex}")
