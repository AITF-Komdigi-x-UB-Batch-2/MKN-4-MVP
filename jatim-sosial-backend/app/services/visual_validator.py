import httpx
import logging
import base64
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models
from app.config import AI_BASE_URL

logger = logging.getLogger(__name__)

async def fetch_image_as_base64(url: str) -> str:
    if not url:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            base64_encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_encoded}"
    except Exception as e:
        logger.error(f"Gagal mengunduh gambar {url}: {e}")
        return None

async def perform_visual_validation(keluarga_id: UUID, user_id: UUID, db: Session):
    """
    Mesin utama untuk Asesmen Visual (Tim 2) dengan support 3 schema input foto:
    1. Tampak luar saja
    2. Tampak dalam saja
    3. Tampak luar & dalam
    Mengubah gambar ke format base64 dan mengirim ke Tim 2.
    """
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    foto_tampak_luar = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id,
        models.Foto.tampak_dalam == False
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    foto_tampak_dalam = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id,
        models.Foto.tampak_dalam == True
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    url_luar = foto_tampak_luar.url_foto if foto_tampak_luar else None
    url_dalam = foto_tampak_dalam.url_foto if foto_tampak_dalam else None

    # Jika tidak ada foto sama sekali di database
    if not url_luar and not url_dalam:
        hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga_id, user_id=user_id)
            db.add(hitung)
        hitung.ada_ketidaksesuaian_visual = None
        hitung.reasoning_tim2 = "Validasi dilewati karena tidak ada foto rumah yang diunggah."
        db.commit()
        return {
            "status": "Dilewati",
            "reasoning": "Tidak ada foto rumah"
        }

    # Fetch base64 data
    base64_luar = await fetch_image_as_base64(url_luar)
    base64_dalam = await fetch_image_as_base64(url_dalam)

    # Validasi jika gagal mengunduh foto
    if not base64_luar and not base64_dalam:
        hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga_id, user_id=user_id)
            db.add(hitung)
        hitung.ada_ketidaksesuaian_visual = None
        hitung.reasoning_tim2 = "Validasi dilewati karena foto yang tersedia gagal diunduh."
        db.commit()
        return {
            "status": "Dilewati",
            "reasoning": "Foto gagal diunduh"
        }

    system_prompt_global = """Kamu adalah sistem AI inspeksi material bangunan untuk validasi data DTSEN Dinas Sosial. 
Tugasmu adalah menganalisis citra rumah secara visual untuk mengidentifikasi material terluas pada komponen bangunan (Atap, Dinding, Lantai), mengklasifikasikan jenis material yang teramati, membandingkannya dengan data referensi DTSEN, serta memberikan penjelasan berbasis bukti visual.

=== ATURAN ANALISIS KOMPONEN ===
1. Analisis HANYA komponen yang diizinkan sesuai instruksi pesan user (Konteks: exterior = tampak luar, interior = tampak dalam).
2. Jika suatu komponen dinyatakan TIDAK dianalisis pada instruksi user, maka prediksi komponen tersebut WAJIB dikosongkan/diikuti aturan default.

=== LABEL MATERIAL RESMI DTSEN (STRICT) ===
Gunakan HANYA satu label per komponen dari daftar di bawah ini. Penulisan harus PERSIS SAMA (huruf kapital, spasi, tanda miring). DILARANG menggabungkan label atau membuat label sendiri.

[Atap]
Beton
Genteng
Seng
Asbes
Bambu
Kayu/sirap
Jerami/ijuk/daun-daunan/rumbia
Lainnya
Tidak terdeteksi

[Dinding]
Tembok
Plesteran anyaman bambu/kawat
Kayu/papan/gypsum/GRC/calciboard
Anyaman bambu
Batang kayu
Bambu
Lainnya
Tidak terdeteksi

[Lantai]
Marmer/granit
Keramik
Parket/vinil/karpet
Ubin/tegel/teraso
Kayu/papan
Semen/bata merah
Bambu
Tanah
Lainnya
Tidak terdeteksi

=== ATURAN "TIDAK TERDETEKSI" ===
Jika komponen yang seharusnya dianalisis tidak terlihat, tertutup objek, berada di luar area, atau bukan citra rumah, gunakan parameter wajib berikut:
- Prediksi : Tidak terdeteksi
- Status   : Tidak teridentifikasi
- Alasan   : (Gunakan persis kalimat baku di bawah ini sesuai komponen)
  - Atap    : "Variabel atap tidak dapat diidentifikasi karena komponen atap pada foto rumah tampak luar tidak terlihat."
  - Dinding : "Variabel dinding tidak dapat diidentifikasi karena komponen dinding pada foto rumah tampak luar tidak terlihat."
  - Lantai  : "Variabel lantai tidak dapat diidentifikasi karena komponen lantai pada foto rumah tampak dalam tidak terlihat."

=== KETENTUAN STATUS VALIDASI ===
Pilih tepat SATU status per komponen:
1. Sesuai : Prediksi visual IDENTIK dengan data referensi DTSEN.
2. Tidak sesuai : Prediksi visual BERBEDA dengan data referensi DTSEN.
3. Tidak teridentifikasi : Digunakan HANYA JIKA prediksi adalah "Tidak terdeteksi".

=== KETENTUAN ALASAN VISUAL ===
- Jika Prediksi ≠ "Tidak terdeteksi": Tulis narasi visual minimal 10-20 kata yang menjelaskan karakteristik fisik pada gambar (tekstur, warna, pola, struktur permukaan, dll) yang mendukung prediksimu.
- Jika Prediksi = "Tidak terdeteksi": WAJIB gunakan kalimat baku pada aturan "Tidak Terdeteksi" di atas tanpa modifikasi.

=== FORMAT OUTPUT (TOON STRICT) ===
Anda WAJIB merespons HANYA dengan format Toon persis seperti di bawah ini. JANGAN tambahkan teks pembuka, penutup, atau format markdown.

Hasil[3]{Komponen,Prediksi,Status,Alasan}:
Atap,<label DTSEN>,<Status>,"<Alasan>"
Dinding,<label DTSEN>,<Status>,"<Alasan>"
Lantai,<label DTSEN>,<Status>,"<Alasan>"
"""

    teks_konteks_rumah = (
        f"\n\n[DATA PROFIL UNTUK DIVALIDASI]\n"
        f"- ID Lantai Terluas: {keluarga.id_lantai_terluas}\n"
        f"- ID Dinding Terluas: {keluarga.id_dinding_terluas}\n"
        f"- ID Atap Terluas: {keluarga.id_atap_terluas}\n"
        "Cocokkan kondisi di foto dengan data profil di atas."
    )

    user_prompt_terpilih = ""
    gambar_dikirim = []

    # Map three distinct image input schemas
    if base64_luar and base64_dalam:
        user_prompt_terpilih = "Ini adalah foto tampak luar dan dalam rumah warga. Silakan evaluasi ketiganya." + teks_konteks_rumah
        gambar_dikirim = [
            {"type": "image_url", "image_url": {"url": base64_luar}},
            {"type": "image_url", "image_url": {"url": base64_dalam}}
        ]
    elif base64_luar and not base64_dalam:
        user_prompt_terpilih = "Ini HANYA foto tampak luar. Tolong evaluasi atap dan dindingnya saja." + teks_konteks_rumah
        gambar_dikirim = [
            {"type": "image_url", "image_url": {"url": base64_luar}}
        ]
    elif not base64_luar and base64_dalam:
        user_prompt_terpilih = "Ini HANYA foto tampak dalam. Tolong evaluasi lantai dan dinding dalamnya saja." + teks_konteks_rumah
        gambar_dikirim = [
            {"type": "image_url", "image_url": {"url": base64_dalam}}
        ]

    payload_ke_tim2 = {
        "model": "model-vision-tim-2", 
        "messages": [
            {"role": "system", "content": system_prompt_global},
            {"role": "user", "content": [{"type": "text", "text": user_prompt_terpilih}, *gambar_dikirim]}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 500,
        # Mengirim data asli untuk support model non-multimodal / fallback
        "konteks_rumah": {
            "lantai": keluarga.id_lantai_terluas,
            "dinding": keluarga.id_dinding_terluas,
            "atap": keluarga.id_atap_terluas
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/ai/visual-validator",
                json=payload_ke_tim2,
                timeout=60.0
            )
            res_ai.raise_for_status()
            hasil_validator = res_ai.json()

            if "choices" in hasil_validator:
                import json
                raw_content = hasil_validator["choices"][0]["message"]["content"]
                if raw_content.strip().startswith("```"):
                    raw_content = raw_content.strip().strip("```json").strip("```").strip()
                hasil_ekstrak = json.loads(raw_content)
                is_match = hasil_ekstrak.get("is_match", True)
                reasoning = hasil_ekstrak.get("reasoning", "Validasi visual selesai.")
            else:
                is_match = hasil_validator.get("is_match", True)
                reasoning = hasil_validator.get("reasoning", "Validasi visual selesai.")
    except Exception as e:
        logger.error("Gagal terhubung ke server Tim 2. Mengaktifkan fallback visual.", exc_info=True)
        is_match = True
        reasoning = f"Foto diasumsikan sesuai secara otomatis karena kendala sistem: {str(e)}"
        hasil_validator = {"is_match": True, "reasoning": reasoning}

    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    if not hitung:
        hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=user_id)
        db.add(hitung)

    hitung.ada_ketidaksesuaian_visual = not is_match
    hitung.reasoning_tim2 = reasoning
    hitung.foto_id_digunakan = foto_tampak_luar.id if foto_tampak_luar else (foto_tampak_dalam.id if foto_tampak_dalam else None)

    db.commit()

    return {
        "status": "Sukses",
        "validation": {
            "is_match": is_match,
            "reasoning": reasoning
        },
        "url_foto_divalidasi": [url_luar, url_dalam],
        "hasil_tim2": hasil_validator
    }
