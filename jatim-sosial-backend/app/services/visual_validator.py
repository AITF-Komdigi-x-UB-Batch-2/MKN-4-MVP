import httpx
import logging
import re
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models
from app.config import AI_BASE_URL
from app.utils.enum import AtapEnum, DindingEnum, LantaiEnum

logger = logging.getLogger(__name__)

async def perform_visual_validation(keluarga_id: UUID, user_id: UUID, db: Session):
    """
    Mesin utama untuk Asesmen Visual (Tim 2) dengan support 3 schema input foto:
    1. Tampak luar saja (Single Exterior)
    2. Tampak dalam saja (Single Interior)
    3. Tampak luar & dalam (Multi)
    Menggunakan format payload strict sesuai kontrak API Tim 2.
    """
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    # 1. Mengambil URL gambar langsung dari Database
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

    # Ambil label dari DTSEN
    atap_DTSEN = AtapEnum.label(keluarga.id_atap_terluas)
    dinding_DTSEN = DindingEnum.label(keluarga.id_dinding_terluas)
    lantai_DTSEN = LantaiEnum.label(keluarga.id_lantai_terluas)

    content_array = []

    # === ROUTING SESUAI SCHEMA TIM 2 ===
    if url_luar and url_dalam:
        # SCHEMA MULTI (EXTERIOR + INTERIOR)
        teks_prompt = f"""Berikut data rumah yang harus divalidasi.

House ID : {keluarga.id}
View Type : exterior + interior

DATA REFERENSI DTSEN :

Atap : {atap_DTSEN}
Dinding : {dinding_DTSEN}
Lantai : {lantai_DTSEN}

INSTRUKSI TUGAS :
Gunakan seluruh gambar yang diberikan untuk membantu memahami struktur rumah dan lokasi komponen.

Untuk setiap komponen, lakukan identifikasi berdasarkan komponen fisik yang benar, dengan prioritas observasi berikut:
Atap: Tentukan material terluas atap utama bangunan. Prioritaskan atap yang menaungi bangunan utama dan abaikan kanopi atau atap tambahan jika atap utama masih terlihat.
Dinding: Tentukan material terluas dinding luar bangunan (fasad utama), bukan sekat interior, furnitur, pagar, dekorasi, atau elemen non-struktural. Pilih material dominan berdasarkan luas area terlihat terbesar.
Lantai: Tentukan material terluas lantai utama di dalam rumah. Prioritaskan material dasar yang terlihat jelas, bukan karpet jika masih ada material dasar yang tampak.

Untuk setiap komponen:
- Tentukan label material resmi DTSEN berdasarkan LABEL AKTUAL yang sudah diberikan.
- Tentukan Status yang sudah tersedia pada metadata.
- Berikan penjelasan visual yang mendukung hasil label aktual untuk digunakan pada field Alasan.

KETENTUAN OUTPUT:
- Gunakan format Toon.
- Jangan menambah komponen lain di luar Atap Dinding dan Lantai.
- Output harus hanya berisi penjelasan visual tanpa menyalin metadata mentah.

Output berupa format output Toon"""
        
        content_array = [
            {"type": "image", "image": url_luar},
            {"type": "text", "text": "Foto tampak luar."},
            {"type": "image", "image": url_dalam},
            {"type": "text", "text": "Foto tampak dalam."},
            {"type": "text", "text": teks_prompt}
        ]

    elif url_luar and not url_dalam:
        # SCHEMA SINGLE EXTERIOR
        teks_prompt = f"""Berikut data rumah yang harus divalidasi.

House ID : {keluarga.id}
View Type : exterior

DATA REFERENSI DTSEN :

Atap : {atap_DTSEN}
Dinding : {dinding_DTSEN}
Lantai : {lantai_DTSEN}

INSTRUKSI TUGAS :

ANALISIS KOMPONEN YANG WAJIB DIANALISIS:
Lakukan analisis material bangunan HANYA pada komponen berikut:
- Atap : Identifikasi label material atap dominan atau material dengan luas area terbesar yang menutupi bangunan. Gunakan atap segitiga (atap utama) sebagai titik acuan. Jika terdapat lembaran atap tambahan yang berada di depan dinding segitiga (seperti kanopi, teras, pelindung masuk, atau atap tambahan lain), ABAIKAN material atap tersebut selama atap utama masih terlihat. Hanya gunakan material kanopi jika atap utama benar-benar tidak terlihat.
- Dinding : Identifikasi label material dinding dominan atau material dengan luas area terbesar yang terlihat pada tampak luar (fasad utama).

Untuk setiap komponen yang dianalisis di atas:
- Tentukan label material resmi DTSEN berdasarkan LABEL AKTUAL yang sudah diberikan.
- Tentukan Status yang sudah tersedia pada metadata.
- Berikan penjelasan visual yang mendukung hasil label aktual untuk digunakan pada field Alasan.

KOMPONEN YANG TIDAK DIANALISIS:
Komponen Lantai TIDAK BOLEH DIANALISIS. Karena variabel lantai pada DTSEN mengacu pada lantai utama di bagian dalam rumah, sedangkan input hanya berupa citra exterior.
Gunakan nilai berikut secara WAJIB untuk komponen lantai :
Prediksi : Tidak terdeteksi
Status : Tidak teridentifikasi
Alasan : "Variabel lantai tidak dapat diidentifikasi karena foto rumah tampak dalam tidak tersedia."

Output berupa format output Toon"""

        content_array = [
            {"type": "image", "image": url_luar},
            {"type": "text", "text": "Foto tampak luar."},
            {"type": "text", "text": teks_prompt}
        ]

    elif not url_luar and url_dalam:
        # SCHEMA SINGLE INTERIOR
        teks_prompt = f"""Berikut data rumah yang harus divalidasi.

House ID : {keluarga.id}
View Type : interior

DATA REFERENSI DTSEN :

Atap : {atap_DTSEN}
Dinding : {dinding_DTSEN}
Lantai : {lantai_DTSEN}

INSTRUKSI TUGAS :

ANALISIS KOMPONEN YANG WAJIB DIANALISIS:
Lakukan analisis material bangunan HANYA pada komponen lantai. Tentukan material lantai utama di dalam rumah berdasarkan material dominan (luas area terlihat terbesar). Jika lantai tertutup lapisan tambahan seperti karpet, identifikasi terlebih dahulu material dasar yang masih terlihat. Jika material dasar tidak dapat diamati, gunakan label Parket/vinil/karpet.

Untuk komponen yang dianalisis:
- Tentukan label material resmi DTSEN berdasarkan LABEL AKTUAL yang sudah diberikan pada komponen Lantai.
- Tentukan Status yang sudah tersedia pada metadata.
- Berikan penjelasan visual yang mendukung hasil label aktual untuk digunakan pada field Alasan.

KOMPONEN YANG TIDAK DIANALISIS:
Komponen Atap dan Dinding TIDAK BOLEH DIANALISIS. Karena input hanya berupa citra interior, maka material atap dan material dinding luar bangunan tidak dapat ditentukan berdasarkan definisi variabel DTSEN.
Gunakan nilai berikut secara WAJIB untuk komponen Atap dan Dinding :
Prediksi : Tidak terdeteksi
Status : Tidak teridentifikasi
Alasan :
Atap → "Variabel atap tidak dapat diidentifikasi karena foto rumah tampak luar tidak tersedia."
Dinding → "Variabel dinding tidak dapat diidentifikasi karena foto rumah tampak luar tidak tersedia."

Output berupa format output Toon"""

        content_array = [
            {"type": "image", "image": url_dalam},
            {"type": "text", "text": "Foto tampak dalam."},
            {"type": "text", "text": teks_prompt}
        ]

    # Merakit Payload Akhir
    system_prompt_global = """Kamu adalah sistem AI inspeksi material bangunan untuk validasi data DTSEN. Tugasmu adalah menganalisis citra rumah secara visual untuk mengidentifikasi material terluas pada komponen bangunan, mengklasifikasikan jenis material yang teramati, membandingkannya dengan data referensi DTSEN, serta memberikan penjelasan berbasis bukti visual pada setiap komponen sebagai alasan hasil validasi.

Analisis komponen harus mengikuti instruksi tugas pada pesan user. Hanya lakukan prediksi pada komponen yang diizinkan untuk dianalisis sesuai skema input. Jika suatu komponen dinyatakan tidak dianalisis
pada instruksi user, maka komponen tersebut wajib mengikuti aturan yang ditetapkan user.

exterior = tampak luar
interior = tampak dalam

LABEL MATERIAL RESMI DTSEN :
Gunakan HANYA satu label per komponen dari daftar berikut. Jangan menggunakan label lain di luar daftar.

Komponen Atap:
Beton
Genteng
Seng
Asbes
Bambu
Kayu/sirap
Jerami/ijuk/daun-daunan/rumbia
Lainnya
Tidak terdeteksi

Komponen Dinding:
Tembok
Plesteran anyaman bambu/kawat
Kayu/papan/gypsum/GRC/calciboard
Anyaman bambu
Batang kayu
Bambu
Lainnya
Tidak terdeteksi

Komponen Lantai:
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

Jika komponen yang seharusnya dianalisis tidak terlihat, tertutup objek lain, berada di luar area citra, atau bukan visual rumah, gunakan:
Prediksi : Tidak terdeteksi
Status   : Tidak teridentifikasi
Alasan : (sesuaikan dengan komponen)
"Atap": "Variabel atap tidak dapat diidentifikasi karena komponen atap pada foto rumah tampak luar tidak terlihat."
"Dinding": "Variabel dinding tidak dapat diidentifikasi karena komponen dinding pada foto rumah tampak luar tidak terlihat."
"Lantai": "Variabel lantai tidak dapat diidentifikasi karena komponen lantai pada foto rumah tampak dalam tidak terlihat."

KETENTUAN STATUS :
Pilih tepat satu status untuk setiap komponen yang dianalisis:
Sesuai : hasil prediksi visual identik atau konsisten dengan data referensi DTSEN.
Tidak sesuai : prediksi visual berbeda dengan data referensi DTSEN.
Tidak teridentifikasi : digunakan ketika prediksi adalah "Tidak terdeteksi",yaitu saat komponen tidak terlihat, bukti visual tidak cukup, atau komponen tidak tersedia sesuai konteks citra dan instruksi user.

KETENTUAN ALASAN :
Untuk setiap komponen, hasilkan penjelasan visual untuk field Alasan:
- Komponen terdeteksi: Tulis minimal 10–20 kata yang menjelaskan karakteristik visual yang mendasari prediksi: tekstur, warna, pola, struktur permukaan, atau ciri material yang terlihat pada citra.
- Komponen tidak terdeteksi (Prediksi = "Tidak terdeteksi"): Gunakan kalimat baku yang tercantum pada instruksi user tanpa modifikasi apapun.

FORMAT OUTPUT :
Gunakan TEPAT format Toon berikut. Tidak ada teks lain di luar format ini.
Hasil[3]{Komponen,Prediksi,Status,Alasan}:
Atap,<label DTSEN>,<Status>,"<Alasan>"
Dinding,<label DTSEN>,<Status>,"<Alasan>"
Lantai,<label DTSEN>,<Status>,"<Alasan>"
"""
    
    payload_ke_tim2 = {
        "model": "model-vision-tim-2", 
        "messages": [
            {"role": "system", "content": system_prompt_global},
            {"role": "user", "content": content_array}
        ],
        "max_tokens": 800
    }

    # 5. Menembak API dan Menangkap Respons
    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/ai/visual-validator",
                json=payload_ke_tim2,
                timeout=60.0
            )
            res_ai.raise_for_status()
            hasil_validator = res_ai.json()

            is_match = True  # Default fallback jika semua komponen sesuai
            reasoning = "Validasi visual selesai."

            if "choices" in hasil_validator:
                raw_content = hasil_validator["choices"][0]["message"]["content"]
                
                # --- PROSES PARSING FORMAT TOON DI DALAM JSON ---

                toon_pattern = re.compile(r'^(Atap|Dinding|Lantai),\s*([^,]+),\s*([^,]+),\s*"(.*)"$', re.MULTILINE)
                matches = toon_pattern.findall(raw_content)

                if matches:
                    # Tempat menampung data hasil ekstrak dari format Toon
                    data_terekstrak = {}
                    for komponen, prediksi, status, alasan in matches:
                        data_terekstrak[komponen.strip()] = {
                            "prediksi": prediksi.strip(),
                            "status": status.strip(),
                            "alasan": alasan.strip()
                        }
                    
                    # Logika menentukan 'is_match' (global): 
                    # Jika ada SATU saja komponen yang statusnya "Tidak sesuai", maka global menjadi False
                    status_komponen = [info["status"] for info in data_terekstrak.values()]
                    if "Tidak sesuai" in status_komponen:
                        is_match = False
                    # Menyusun teks reasoning gabungan untuk disimpan di kolom reasoning_tim2 database
                    reasoning_list = [f"{k}: {v['status']} ({v['alasan']})" for k, v in data_terekstrak.items()]
                    reasoning = " | ".join(reasoning_list)
                else:
                    # Jika format Toon gagal dibaca regex, simpan teks mentahnya agar data tidak hilang
                    reasoning = f"Gagal parsing, menyimpan raw Toon: {raw_content}"
            else:
                is_match = hasil_validator.get("is_match", True)
                reasoning = hasil_validator.get("reasoning", "Validasi visual selesai.")
                
    except Exception as e:
        logger.error("Gagal terhubung ke server Tim 2 atau gagal memproses response.", exc_info=True)
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
