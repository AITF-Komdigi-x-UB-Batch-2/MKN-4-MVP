import uvicorn
import re
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import date

app = FastAPI(
    title="Mock AI Server - Berbasis Basis Data Riil Jatim",
    version="5.2",
    description="Server Mock AI yang disesuaikan dengan skema kolom asli df_merge_v3_20.csv dan mendukung integrasi endpoint Tim 2 & Tim 3."
)

# Wajib ditambahkan agar tidak kena blokir CORS saat diakses lokal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# PEMETAAN & HELPER
# =====================================================================
ATAP_MAP = {1: "Beton", 2: "Genteng", 3: "Seng", 4: "Asbes", 5: "Bambu", 6: "Kayu/Sirap", 7: "Jerami/Rumbia", 8: "Lainnya", 0: "Tidak Terdeteksi"}
DINDING_MAP = {1: "Tembok", 2: "Plesteran Anyaman", 3: "Kayu/Papan", 4: "Anyaman Bambu", 5: "Batang Kayu", 6: "Bambu", 7: "Lainnya", 0: "Tidak Terdeteksi"}
LANTAI_MAP = {1: "Marmer/Granit", 2: "Keramik", 3: "Parket/Vinyl", 4: "Ubin/Tegel", 5: "Kayu/Papan", 6: "Semen", 7: "Bambu", 8: "Tanah", 9: "Lainnya", 10: "Lainnya/Tanpa Lantai", 0: "Tidak Terdeteksi"}

def hitung_umur_dari_payload(payload: dict) -> int:
    if "umur_2026" in payload:
        return int(payload["umur_2026"])
    if "umur" in payload:
        return int(payload["umur"])
        
    tgl_lahir = payload.get("tanggal_lahir")
    if tgl_lahir:
        try:
            tahun = int(str(tgl_lahir).strip()[:4])
            return 2026 - tahun
        except ValueError:
            pass
    return 0

def label_to_id_atap(label: str) -> int:
    label = label.strip().lower()
    if "beton" in label: return 1
    if "genteng" in label: return 2
    if "seng" in label: return 3
    if "asbes" in label: return 4
    if "bambu" in label: return 5
    if "kayu" in label or "sirap" in label: return 6
    if "jerami" in label or "rumbia" in label or "ijuk" in label or "daun" in label: return 7
    if "tidak terdeteksi" in label: return 0
    return 8

def label_to_id_dinding(label: str) -> int:
    label = label.strip().lower()
    if "tembok" in label: return 1
    if "plesteran" in label: return 2
    if "kayu" in label or "papan" in label or "gypsum" in label or "grc" in label or "calciboard" in label: return 3
    if "anyaman" in label: return 4
    if "batang" in label: return 5
    if "bambu" in label: return 6
    if "tidak terdeteksi" in label: return 0
    return 7

def label_to_id_lantai(label: str) -> int:
    label = label.strip().lower()
    if "marmer" in label or "granit" in label: return 1
    if "keramik" in label: return 2
    if "parket" in label or "vinil" in label or "karpet" in label: return 3
    if "ubin" in label or "tegel" in label or "teraso" in label: return 4
    if "kayu" in label or "papan" in label: return 5
    if "semen" in label or "bata" in label: return 6
    if "bambu" in label: return 7
    if "tanah" in label: return 8
    if "tidak terdeteksi" in label: return 0
    return 9

def parse_profil_warga(profil: str) -> dict:
    parsed = {}
    
    nik_kk_match = re.search(r'-\s*NIK\s*/\s*No\.\s*KK\s*:\s*([^\s/]+)\s*/\s*([^\s\n]+)', profil)
    if nik_kk_match:
        parsed['nik'] = nik_kk_match.group(1).strip()
        parsed['no_kk'] = nik_kk_match.group(2).strip()
        
    nama_match = re.search(r'-\s*Nama\s*:\s*(.+)', profil)
    if nama_match:
        parsed['nama'] = nama_match.group(1).strip()
        
    umur_match = re.search(r'-\s*Umur\s*:\s*(\d+)\s*tahun', profil)
    if umur_match:
        parsed['umur'] = int(umur_match.group(1))
        
    desil_dtsen_match = re.search(r'-\s*Desil\s*Nasional\s*:\s*([^\s|]+)\s*\|\s*Status\s*DTSEN\s*:\s*(.+)', profil)
    if desil_dtsen_match:
        desil_str = desil_dtsen_match.group(1).strip()
        parsed['desil'] = int(desil_str) if desil_str.isdigit() else 1
        parsed['status_dtsen'] = desil_dtsen_match.group(2).strip()
        
    bansos_match = re.search(r'-\s*Bansos\s*:\s*(.+)', profil)
    if bansos_match:
        parsed['bansos'] = bansos_match.group(1).strip()
        
    pbi_match = re.search(r'-\s*PBI\s*Jaminan\s*Kes\s*:\s*(.+)', profil)
    if pbi_match:
        pbi_str = pbi_match.group(1).strip().lower()
        parsed['pbi'] = 1 if pbi_str in ('ya', '1', 'true') else 0
        
    has_disability = False
    profil_lower = profil.lower()
    for word in ["sama sekali tidak bisa", "banyak kesulitan", "sedikit kesulitan"]:
        if word in profil_lower:
            has_disability = True
            break
    parsed['id_disabilitas'] = 1 if has_disability else 0
    
    wilayah_match = re.search(r'-\s*Wilayah\s*:\s*(.+)', profil)
    if wilayah_match:
        wilayah = wilayah_match.group(1).strip()
        parsed['wilayah'] = wilayah
        if "jawa timur" in wilayah.lower():
            parsed['kode_provinsi'] = "35"
        else:
            parsed['kode_provinsi'] = "00"
            
    return parsed

def extract_dtsen_labels(payload: dict):
    atap_lbl, dinding_lbl, lantai_lbl = "Genteng", "Tembok", "Keramik"
    house_id = "Unknown"
    
    messages = payload.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            text_to_search = ""
            if isinstance(content, str):
                text_to_search = content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_to_search += "\n" + item.get("text", "")
            
            id_match = re.search(r'House\s*ID\s*:\s*([^\n]+)', text_to_search, re.IGNORECASE)
            if id_match: house_id = id_match.group(1).strip()
                
            atap_match = re.search(r'Atap\s*:\s*([^\n]+)', text_to_search, re.IGNORECASE)
            if atap_match: atap_lbl = atap_match.group(1).strip()
                
            dinding_match = re.search(r'Dinding\s*:\s*([^\n]+)', text_to_search, re.IGNORECASE)
            if dinding_match: dinding_lbl = dinding_match.group(1).strip()
                
            lantai_match = re.search(r'Lantai\s*:\s*([^\n]+)', text_to_search, re.IGNORECASE)
            if lantai_match: lantai_lbl = lantai_match.group(1).strip()
                
    return house_id, atap_lbl, dinding_lbl, lantai_lbl

# =====================================================================
# CORE LOGIC: VISUAL VALIDATOR
# =====================================================================
def run_visual_validator_logic(id_data: str, id_atap: int, id_dinding: int, id_lantai: int) -> dict:
    txt_atap = ATAP_MAP.get(id_atap, "Tidak Terdeteksi")
    txt_dinding = DINDING_MAP.get(id_dinding, "Tidak Terdeteksi")
    txt_lantai = LANTAI_MAP.get(id_lantai, "Tidak Terdeteksi")

    is_match = False
    reasoning = ""
    status_atap, status_dinding, status_lantai = "Sesuai", "Sesuai", "Sesuai"
    reason_atap = f"Kondisi atap terpantau stabil berbahan {txt_atap}."
    reason_dinding = f"Kondisi dinding luar kokoh berbahan {txt_dinding}."
    reason_lantai = f"Kondisi lantai bersih berbahan {txt_lantai}."

    if id_atap == 0 or id_dinding == 0 or id_lantai == 0:
        status_atap = status_dinding = status_lantai = "Tidak teridentifikasi"
        reason_atap = "Variabel atap tidak dapat diidentifikasi karena foto buram."
        reason_dinding = "Variabel dinding tidak dapat diidentifikasi karena foto buram."
        reason_lantai = "Variabel lantai tidak dapat diidentifikasi karena foto buram."
        is_match = False
        reasoning = "Skenario 19 [TIDAK MATCH]: Foto bukti lapangan terdeteksi buram atau gelap. Gagal mengekstrak klasifikasi material."

    elif id_atap == 2 and id_dinding == 1 and id_lantai in [2, 6]:
        is_match = True
        reasoning = f"Skenario 11 [TOTAL MATCH]: Hasil deteksi visual sinkron dengan berkas (Atap: {txt_atap}, Dinding: {txt_dinding}, Lantai: {txt_lantai})."
        reason_atap = f"Kesesuaian penuh terdeteksi. Bahan atap: {txt_atap}."
        reason_dinding = f"Kesesuaian penuh terdeteksi. Bahan dinding: {txt_dinding}."
        reason_lantai = f"Kesesuaian penuh terdeteksi. Bahan lantai: {txt_lantai}."

    elif id_atap == 3 and id_dinding == 1 and id_lantai == 2:
        status_atap = "Tidak sesuai"
        is_match = False
        reasoning = f"Skenario 12 [MISMATCH ATAP]: Berkas tertulis atap Genteng, namun lensa AI mendeteksi atap berbahan {txt_atap}."
        reason_atap = f"Berkas tertulis atap Genteng, namun lensa AI mendeteksi atap berbahan {txt_atap}."

    elif id_atap == 2 and id_dinding == 4 and id_lantai == 2:
        status_dinding = "Tidak sesuai"
        is_match = False
        reasoning = f"Skenario 13 [MISMATCH DINDING]: Administrasi mencatat Tembok Permanen, realita lapangan berupa {txt_dinding}."
        reason_dinding = f"Administrasi mencatat Tembok Permanen, realita lapangan berupa {txt_dinding}."

    elif id_atap == 2 and id_dinding == 1 and id_lantai == 8:
        status_lantai = "Tidak sesuai"
        is_match = False
        reasoning = f"Skenario 14 [MISMATCH LANTAI]: Lantai asli objek berupa {txt_lantai}, bukan lantai ubin/keramik."
        reason_lantai = f"Lantai asli objek berupa {txt_lantai}, bukan lantai ubin/keramik."

    elif id_atap == 1 and id_dinding == 1 and id_lantai == 1:
        status_atap = status_dinding = status_lantai = "Tidak sesuai"
        is_match = False
        reasoning = "Skenario 17 [TOTAL MISMATCH]: Tercatat miskin ekstrem namun verifikasi objek mendeteksi hunian mewah (Atap Beton, Lantai Marmer)."
        reason_atap = "Terdeteksi atap Beton mewah."
        reason_dinding = "Terdeteksi dinding Tembok mewah."
        reason_lantai = "Terdeteksi lantai Marmer mewah."

    else:
        is_match = True if (id_atap == 2 or id_dinding == 1) else False
        reasoning = f"Skenario 18 [EVALUASI PARSIAL]: Algoritma mendeteksi Atap: {txt_atap}, Dinding: {txt_dinding}, Lantai: {txt_lantai}."
        status_atap = "Sesuai" if id_atap == 2 else "Tidak sesuai"
        status_dinding = "Sesuai" if id_dinding == 1 else "Tidak sesuai"
        status_lantai = "Sesuai"

    return {
        "is_match": is_match,
        "reasoning": reasoning,
        "status_atap": status_atap,
        "status_dinding": status_dinding,
        "status_lantai": status_lantai,
        "reason_atap": reason_atap,
        "reason_dinding": reason_dinding,
        "reason_lantai": reason_lantai
    }

# =====================================================================
# CORE LOGIC: ANALISIS BANTUAN
# =====================================================================
def run_analisis_bantuan_logic(payload: dict) -> dict:
    nik = str(payload.get("nik", ""))
    desil = int(payload.get("desil_nasional", payload.get("desil", 1)))
    pkh_plus = int(payload.get("pkh_plus", 0))
    bansos = str(payload.get("bansos", "")).upper()
    id_disabilitas = int(payload.get("id_disabilitas", 0))
    status_dtsen = str(payload.get("status_dtsen", "DTSEN AKTIF")).upper()
    kode_provinsi = str(payload.get("kode_provinsi", "35"))
    umur = hitung_umur_dari_payload(payload)
    
    status_pkh, status_aspd = "Ditolak", "Ditolak"
    skor_pkh, skor_aspd = 0.0, 0.0
    reasoning = ""

    if "AKTIF" not in status_dtsen:
        reasoning = "Skenario 9 [DITOLAK]: Status kepesertaan DTSEN warga terdata tidak aktif pada database Pusdatin."
    elif kode_provinsi != "35" and not nik.startswith("35"):
        reasoning = "Skenario 7 [DITOLAK]: Data administratif menunjukkan kode wilayah luar Provinsi Jawa Timur."
    elif desil > 5:
        reasoning = f"Skenario 6 [DITOLAK]: Tingkat kesejahteraan ekonomi berada pada Desil {desil} (Kategori Mampu)."
    elif umur >= 70 and ("PKH" in bansos or pkh_plus == 1) and (1 <= desil <= 4) and id_disabilitas > 0:
        status_pkh, status_aspd = "Eligible", "Eligible"
        skor_pkh, skor_aspd = 89.20, 94.50
        reasoning = "Skenario 3 [LOLOS KEDUANYA]: Subjek memenuhi juknis Lansia PKH+ (Usia >= 70) dan terdata sebagai penyandang disabilitas berat (ASPD)."
    elif umur >= 70 and ("PKH" in bansos or pkh_plus == 1) and (1 <= desil <= 4):
        status_pkh = "Eligible"
        skor_pkh = 84.70
        reasoning = f"Skenario 1 [ELIGIBLE PKH+]: Lansia berumur {umur} tahun, terverifikasi masuk kloter desil {desil}, dan menerima komponen bantuan sosial dasar."
    elif (0 <= umur <= 60) and (1 <= desil <= 5) and id_disabilitas > 0:
        status_aspd = "Eligible"
        skor_aspd = 78.30
        reasoning = "Skenario 2 [ELIGIBLE ASPD]: Masuk kriteria usia produktif disabilitas, tercatat memiliki hambatan fungsional tubuh, layak menerima tunjangan ASPD."
    elif umur < 70 and ("PKH" in bansos or pkh_plus == 1):
        reasoning = f"Skenario 4 [DITOLAK PKH+]: Bansos dasar PKH aktif, namun usia riil sistem baru mencapai {umur} tahun (Syarat wajib >= 70 tahun)."
    elif umur >= 70 and not ("PKH" in bansos or pkh_plus == 1):
        reasoning = "Skenario 8 [DITOLAK PKH+]: Usia memenuhi kriteria lansia, namun variabel juknis bansos dasar PKH dari pusat bernilai kosong."
    elif (0 <= umur <= 60) and id_disabilitas == 0:
        reasoning = "Skenario 5 [DITOLAK ASPD]: Pemohon berada di rentang usia produktif namun indikator disabilitas pada data administratif bernilai 0 (Sehat)."
    else:
        status_aspd = "Ground Check"
        skor_aspd = 48.00
        reasoning = "Skenario 10 [GROUND CHECK]: Parameter data administrasi berada pada ambang batas kerentanan. Sistem merekomendasikan verifikasi faktual lapangan."

    return {
        "status": "success",
        "eligible_pkh_plus": status_pkh == "Eligible",
        "eligible_aspd": status_aspd == "Eligible",
        "status_pkh_plus": status_pkh,
        "status_aspd": status_aspd,
        "skor_pkh_plus": skor_pkh,
        "skor_aspd": skor_aspd,
        "ai_reasoning": reasoning
    }


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.post("/api/ai/analisis-bantuan", tags=["Analisis Bantuan Kelayakan"])
async def mock_analisis_bantuan(payload: dict = Body(...)):
    return run_analisis_bantuan_logic(payload)


@app.post("/api/ai/visual-validator", tags=["Tim 2 - Visual Validator"])
async def mock_visual_validator(payload: dict = Body(...)):
    id_data = payload.get("id_data", "Unknown")
    id_atap = int(payload.get("id_atap_terluas", 2))
    id_dinding = int(payload.get("id_dinding_terluas", 1))
    id_lantai = int(payload.get("id_lantai_terluas", 2))

    res = run_visual_validator_logic(id_data, id_atap, id_dinding, id_lantai)
    return {
        "status": "success",
        "id_data": id_data,
        "is_match": res["is_match"],
        "reasoning": res["reasoning"]
    }


@app.post("/recommend", tags=["Tim 3 - Recommend Mock"])
async def mock_recommend(payload: dict = Body(...)):
    profil_warga = payload.get("profil_warga", "")
    parsed = parse_profil_warga(profil_warga)
    
    # Memanggil core logic langsung tanpa bentrok dengan FastAPI Routing
    res = run_analisis_bantuan_logic(parsed)
    
    rekomendasi = []
    rekomendasi.append({"nama_program": "PKH Plus", "status": "ELIGIBLE" if res.get("eligible_pkh_plus") else "NOT_ELIGIBLE"})
    rekomendasi.append({"nama_program": "ASPD", "status": "ELIGIBLE" if res.get("eligible_aspd") else "NOT_ELIGIBLE"})
        
    return {
        "rekomendasi": rekomendasi,
        "ringkasan_profil": f"Analisis sosial berdasarkan profil warga: {res.get('ai_reasoning')}",
        "rekomendasi_teknis_bansos": res.get("ai_reasoning")
    }


@app.post("/v1/chat/completions", tags=["Tim 2 - Chat Completions Mock"])
async def mock_chat_completions(payload: dict = Body(...)):
    if "messages" in payload:
        house_id, atap_lbl, dinding_lbl, lantai_lbl = extract_dtsen_labels(payload)
        id_atap = label_to_id_atap(atap_lbl)
        id_dinding = label_to_id_dinding(dinding_lbl)
        id_lantai = label_to_id_lantai(lantai_lbl)
        
        res = run_visual_validator_logic(house_id, id_atap, id_dinding, id_lantai)
        
        content = (
            f"Atap,{atap_lbl},{res['status_atap']},\"{res['reason_atap']}\"\n"
            f"Dinding,{dinding_lbl},{res['status_dinding']},\"{res['reason_dinding']}\"\n"
            f"Lantai,{lantai_lbl},{res['status_lantai']},\"{res['reason_lantai']}\""
        )
        return {
            "choices": [{"message": {"content": content}}]
        }
    else:
        id_data = payload.get("id_data", "Unknown")
        id_atap = int(payload.get("id_atap_terluas", 2))
        id_dinding = int(payload.get("id_dinding_terluas", 1))
        id_lantai = int(payload.get("id_lantai_terluas", 2))
        
        res = run_visual_validator_logic(id_data, id_atap, id_dinding, id_lantai)
        return {
            "status": "success",
            "id_data": id_data,
            "is_match": res["is_match"],
            "reasoning": res["reasoning"]
        }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server Jatim (CSV Validated) is running perfectly on Port 8001!"}


if __name__ == "__main__":
    print(" MENYALAKAN SERVER AI MOCK BERBASIS DATA RIIL PORT 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)