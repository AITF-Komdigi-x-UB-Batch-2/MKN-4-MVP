import csv
import io
import sys
import os

# Simulasi MAPPING_DTKS
MAPPING_DTKS = {
    "no_kk": "nomor_kartu_keluarga",
    "nama": "nama_anggota_keluarga",
    "pbi": "pbi_nas",
    "id_status_penguasaan_bangunan": "status_kepemilikan_rumah",
    "id_lantai_terluas": "jenis_lantai_terluas",
    "luas_lantai_bangunan": "luas_lantai",
    "id_dinding_terluas": "jenis_dinding_terluas",
    "id_atap_terluas": "jenis_atap_terluas",
    "id_sumber_airminum": "sumber_air_minum_utama",
    "id_sumberpenerangan": "sumber_penerangan_utama",
    "id_bb_utama": "bahan_bakar_utama_memasak",
    "id_fasilitas_bab": "fasilitas_bab",
    "id_jenis_kloset": "jenis_kloset",
    "id_pembuangan_tinja": "pembuangan_akhir_tinja",
    "lahan_tempat_lain": "aset_tidak_bergerak_lahan_lainnya",
    "rumah_tempat_lain": "aset_tidak_bergerak_rumah_lainnya",
    "jml_sapi": "jumlah_ternak_sapi",
    "jml_kerbau": "jumlah_ternak_kerbau",
    "jml_kuda": "jumlah_ternak_kuda",
    "jml_babi": "jumlah_ternak_babi",
    "jml_kambing_domba": "jumlah_ternak_kambing_domba",
    "Foto_Rumah": "url_foto_rumah"
}

# Simulasi kolom_sah
kolom_sah = [
    'id', 'nomor_kartu_keluarga', 'periode', 'kode_provinsi', 'provinsi', 
    'kode_kabupaten_kota', 'kabupaten_kota', 'kode_kecamatan', 'kecamatan', 
    'kode_kelurahan_desa', 'kelurahan_desa', 'alamat', 'jumlah_anggota_keluarga', 
    'nama_anggota_keluarga', 'pbi_nas', 'pbi_pemda', 'id_pelanggan_pln', 
    'status_kepemilikan_rumah', 'jenis_lantai_terluas', 'luas_lantai', 
    'jenis_dinding_terluas', 'jenis_atap_terluas', 'sumber_air_minum_utama', 
    'sumber_penerangan_utama', 'daya_terpasang', 'bahan_bakar_utama_memasak', 
    'fasilitas_bab', 'jenis_kloset', 'pembuangan_akhir_tinja', 'kepemilikan_aset', 
    'aset_bergerak_tabung_gas', 'aset_bergerak_lemari_es', 'aset_bergerak_ac', 
    'aset_bergerak_pemanas_air', 'aset_bergerak_telepon_rumah', 'aset_bergerak_tv_datar', 
    'aset_bergerak_emas_perhiasan', 'aset_bergerak_komputer_laptop_tablet', 
    'aset_bergerak_sepeda_motor', 'aset_bergerak_sepeda', 'aset_bergerak_mobil', 
    'aset_bergerak_perahu', 'aset_bergerak_kapal_perahu_motor', 'aset_bergerak_smartphone', 
    'aset_tidak_bergerak_lahan_lainnya', 'aset_tidak_bergerak_rumah_lainnya', 
    'jumlah_ternak_sapi', 'jumlah_ternak_kerbau', 'jumlah_ternak_kuda', 'jumlah_ternak_babi', 
    'jumlah_ternak_kambing_domba', 'desil_nasional'
]

file_path = r"d:\Coding\MVP-Apps-Pemetaan_Kemiskinan_dan_Bantuan\datadummy_alvin_sample.csv"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    csv_reader = csv.DictReader(f)
    reader = list(csv_reader)

print(f"Total rows read from CSV: {len(reader)}")

sukses = 0
di_skip = 0

for idx, raw_row in enumerate(reader):
    try:
        row = {}
        for k, v in raw_row.items():
            if k is not None:
                db_key = MAPPING_DTKS.get(k, k)
                row[db_key] = v

        no_kk_row = row.get("nomor_kartu_keluarga")
        if not no_kk_row:
            print(f"Row {idx}: no_kk_row is empty. Keys in row: {list(row.keys())[:10]}...")
            di_skip += 1
            continue

        raw_urls = row.pop("url_foto_rumah", "")
        
        data_bersih = {}
        for k, v in row.items():
            if k not in kolom_sah:
                continue
            val_str = str(v).strip().upper() if v else ""

            if k.startswith("kode_"):
                data_bersih[k] = val_str.replace(".", "")
            elif k.startswith("aset_") or k.startswith("pbi_") or k == "kepemilikan_aset":
                data_bersih[k] = val_str in ["YA", "1", "TRUE"]
            elif k in ["desil_nasional"]:
                try: data_bersih[k] = int(float(v)) if v else None
                except: data_bersih[k] = None
            elif k.startswith("jumlah_") or k in ["luas_lantai", "daya_terpasang", "status_kepemilikan_rumah", "jenis_lantai_terluas", "jenis_dinding_terluas", "jenis_atap_terluas", "sumber_air_minum_utama", "sumber_penerangan_utama", "bahan_bakar_utama_memasak", "fasilitas_bab", "jenis_kloset", "pembuangan_akhir_tinja"]:
                try: data_bersih[k] = int(float(v)) if v else 0
                except: data_bersih[k] = 0
            else:
                data_bersih[k] = v

        print(f"Row {idx}: Berhasil dibersihkan. KK: {no_kk_row}")
        sukses += 1
    except Exception as e:
        print(f"Row {idx}: Exception: {e}")
        di_skip += 1

print(f"\nSukses: {sukses}, Di-skip: {di_skip}")
