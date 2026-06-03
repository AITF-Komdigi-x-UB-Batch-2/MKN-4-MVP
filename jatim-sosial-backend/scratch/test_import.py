import sys
import os
import asyncio
import httpx

async def main_test():
    try:
        # Let's read df_sample_10_skor.csv
        csv_path = "df_sample_10_skor.csv"
        with open(csv_path, "rb") as f:
            content = f.read()
        
        print("Importing CSV...")
        import csv
        import io
        csv_reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        reader = list(csv_reader)
        
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
            "Foto_Rumah": "url_foto_rumah",
            "foto_rumah": "url_foto_rumah",
            "url_foto_rumah": "url_foto_rumah"
        }

        async with httpx.AsyncClient() as client:
            for idx_row, raw_row in enumerate(reader):
                row = {}
                for k, v in raw_row.items():
                    if k:
                        db_key = MAPPING_DTKS.get(str(k).strip(), str(k).strip())
                        row[db_key] = v
                
                no_kk_row = row.get("nomor_kartu_keluarga")
                if not no_kk_row:
                    continue
                
                raw_urls = row.get("url_foto_rumah", "")
                raw_urls_dalam = row.get("foto_rumah_tampak_dalam", "")
                
                # Check if it has values
                if not raw_urls and not raw_urls_dalam:
                    continue
                    
                print(f"\nRow {idx_row+1} (KK: {no_kk_row}):")
                print(f"  raw_urls: {raw_urls}")
                print(f"  raw_urls_dalam: {raw_urls_dalam}")
                
                all_urls = []
                if raw_urls:
                    all_urls.extend([u.strip(" []\"'") for u in str(raw_urls).split(",") if u.strip(" []\"'")])
                if raw_urls_dalam:
                    all_urls.extend([u.strip(" []\"'") for u in str(raw_urls_dalam).split(",") if u.strip(" []\"'")])
                
                print(f"  Parsed all_urls: {all_urls}")
                
                for idx, url in enumerate(all_urls):
                    print(f"  Downloading {url}...")
                    try:
                        res = await client.get(url, follow_redirects=True, timeout=15.0)
                        print(f"    Status: {res.status_code}, Length: {len(res.content)}")
                    except Exception as e:
                        print(f"    Error: {e}")
                        
    except Exception as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    asyncio.run(main_test())
