"""
FILE: app/routers/items.py
DESKRIPSI:
Mengelola data warga (keluarga), pengunggahan foto, sinkronisasi file CSV/Excel DTKS,
dan integrasi detail data bantuan sosial serta validasi status keluarga.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import csv
import io
import os
import tempfile
from app.database import get_db
from app import models
from app.security import get_current_user
from app.config import MINIO_BUCKET, MINIO_ENDPOINT, MINIO_PUBLIC_ENDPOINT, s3_client, to_public_foto_url
from app.schemas import item as item_schema
from app.services.task_queue import run_async_visual_validation, run_async_assessment
from app.services.ai_client import determine_eligibility
from app.utils.normalizer import fix_nik, safe_int, is_not_null, to_int
from app.utils.scoring import hitung_skor_bantuan
import httpx
import logging
import uuid
import re
import pandas as pd


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["3. Data Warga & Bantuan"]
)

@router.post(
    "/import-csv",
    summary="Sinkronisasi data warga dan foto dari file CSV atau Excel (XLSX)"
)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(temp_path)
        else:
            try:
                df = pd.read_csv(temp_path, encoding="utf-8-sig")
                if len(df.columns) <= 1:
                    df = pd.read_csv(temp_path, encoding="utf-8-sig", sep=";")
            except UnicodeDecodeError:
                df = pd.read_csv(temp_path, encoding="latin1")
                if len(df.columns) <= 1:
                    df = pd.read_csv(temp_path, encoding="latin1", sep=";")
        
        df = df.fillna("")
        reader = df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca berkas: {str(e)}")
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

    kolom_sah = [c.name for c in models.Keluarga.__table__.columns]
    sukses = 0
    di_skip = 0
    log_foto = []
    keluarga_ids_for_tasks = set()

# Kolom aset yang harus jadi INTEGER (0/1), bukan boolean
    KOLOM_ASET_INT = {
        "kepemilikan_aset",
        "aset_bergerak_tabung_gas", "aset_bergerak_lemari_es", "aset_bergerak_ac",
        "aset_bergerak_pemanas_air", "aset_bergerak_telepon_rumah", "aset_bergerak_tv_datar",
        "aset_bergerak_emas_perhiasan", "aset_bergerak_komputer_laptop_tablet",
        "aset_bergerak_sepeda_motor", "aset_bergerak_sepeda", "aset_bergerak_mobil",
        "aset_bergerak_perahu", "aset_bergerak_kapal_perahu_motor", "aset_bergerak_smartphone",
    }

    # Kolom yang harus jadi INTEGER (sesuai kolom DB terbaru)
    KOLOM_INT = {
        "umur_2026", "pkh_plus", "desil_nasional_anggota", "desil_nasional_keluarga",
        "kemiskinan_ekstrem", "id_jenis_kelamin", "id_hub_kepala_keluarga",
        "id_disabilitas", "pbi", "id_status_perkawinan", "id_partisipasi_sekolah",
        "id_jenjang_pendidikan_dukcapil", "membantu_bekerja",
        "id_lapangan_usaha_dari_usaha_utama", "id_status_kedudukan_pekerjaan_utama",
        "id_kepemilikan_izin_usaha", "jumlah_jenis_usaha", "id_pekerjaan_utama",
        "jumlah_pekerja_dibayar", "jumlah_pekerja_tidak_dibayar",
        "luas_lantai_bangunan", "id_dayapenerangan",
        "lahan_tempat_lain", "rumah_tempat_lain",
        "jml_sapi", "jml_kerbau", "jml_kuda", "jml_babi", "jml_kambing_domba",
        "id_status_penguasaan_bangunan", "id_lantai_terluas", "id_dinding_terluas",
        "id_atap_terluas", "id_sumber_airminum", "id_sumberpenerangan", 
        "id_bb_utama", "id_fasilitas_bab", "id_jenis_kloset", "id_pembuangan_tinja",
        "pbi", "desil_nasional_anggota", "desil_nasional_keluarga", "umur_2026",
        "id_jenis_kelamin", "id_hub_kepala_keluarga", "id_disabilitas",
        "id_status_perkawinan", "id_partisipasi_sekolah", "id_jenjang_pendidikan_dukcapil",
        "membantu_bekerja", "id_lapangan_usaha_dari_usaha_utama", "id_status_kedudukan_pekerjaan_utama",
        "id_kepemilikan_izin_usaha", "id_pekerjaan_utama", "id_omset_usaha_utama",
        "id_kondisi_gizi", "id_penglihatan", "id_pendengaran", "id_berjalan_atau_naik_tangga",
        "id_menggunakan_tangan_jari", "id_belajar_kemampuan_intelektual", "id_pengendalian_perilaku",
        "id_berbicara_komunikasi", "id_mengurus_diri", "id_mengingat_berkonsentrasi",
        "id_kesedihan_depresi", "id_penyakit_menahun", "id_status_keberadaan_keluarga",
        "kpm_jawara", "putri_jawara", "aspd", "eks_ppks_jawara", "ppks_jawara",
        "kemiskinan_ekstrem", "pkh_plus"
    }

    # Mapping dari header CSV/Excel DTKS ke kolom Database
    MAPPING_DTKS = {
        "NIK": "nik",
        "Nik": "nik",
        "no_kk": "no_kk",
        "nomor_kartu_keluarga": "no_kk",
        "nama": "nama",
        "nama_kepala_keluarga": "nama",
        "pbi": "pbi",
        "desil_nasional": "desil_nasional_keluarga",
        "desil_nasional_anggota": "desil_nasional_anggota",
        "desil_nasional_keluarga": "desil_nasional_keluarga",
        "id_status_penguasaan_bangunan": "id_status_penguasaan_bangunan",
        "id_lantai_terluas": "id_lantai_terluas",
        "luas_lantai_bangunan": "luas_lantai_bangunan",
        "id_dinding_terluas": "id_dinding_terluas",
        "id_atap_terluas": "id_atap_terluas",
        "id_sumber_airminum": "id_sumber_airminum",
        "id_sumberpenerangan": "id_sumberpenerangan",
        "id_bb_utama": "id_bb_utama",
        "id_fasilitas_bab": "id_fasilitas_bab",
        "id_jenis_kloset": "id_jenis_kloset",
        "id_pembuangan_tinja": "id_pembuangan_tinja",
        "lahan_tempat_lain": "lahan_tempat_lain",
        "rumah_tempat_lain": "rumah_tempat_lain",
        "jml_sapi": "jml_sapi",
        "jml_kerbau": "jml_kerbau",
        "jml_kuda": "jml_kuda",
        "jml_babi": "jml_babi",
        "jml_kambing_domba": "jml_kambing_domba",
        "Foto_Rumah": "url_foto_rumah",
        "foto_rumah": "url_foto_rumah",
        "url_foto_rumah": "url_foto_rumah",
        "Foto_rumah": "url_foto_rumah",
        "FOTO_RUMAH": "url_foto_rumah",
        "foto_rumah_tampak_dalam": "foto_rumah_tampak_dalam",
        "Foto_rumah_tampak_dalam": "foto_rumah_tampak_dalam",
        "Foto_Rumah_Tampak_Dalam": "foto_rumah_tampak_dalam",
        "FOTO_RUMAH_TAMPAK_DALAM": "foto_rumah_tampak_dalam",
        "desil_nasional_keluarga": "desil_nasional_keluarga",
        "desil_nasional_anggota": "desil_nasional_anggota",
        "umur_2026": "umur_2026",
        "cut_off_keluarga": "cut_off_keluarga"
    }


    async with httpx.AsyncClient() as client:
        for idx_row, raw_row in enumerate(reader):
            try:
                row = {}
                for k, v in raw_row.items():
                    if k:
                        cleaned_key = str(k).strip().lstrip("\ufeff")
                        db_key = MAPPING_DTKS.get(cleaned_key, cleaned_key)
                        row[db_key] = v

                if idx_row < 3:
                    log_foto.append(f"[DEBUG] Row {idx_row+1} keys: {list(row.keys())[10:]}")

                no_kk_row = (row.get("no_kk") or row.get("nomor_kartu_keluarga") or "").strip()
                if not no_kk_row or no_kk_row.lower() == "nan":
                    di_skip += 1
                    log_foto.append(
                        f"Baris {idx_row + 1} di-skip: 'no_kk' kosong. Header terdeteksi: {list(row.keys())[:10]}"
                    )
                    continue

                # --- MENGGUNAKAN METODE POP ---
                raw_urls = row.pop("url_foto_rumah", "")
                raw_urls_dalam = row.pop("foto_rumah_tampak_dalam", "")

                # 1. Bersihkan Data Keluarga
                data_bersih = {}
                for k, v in row.items():
                    if k not in kolom_sah:
                        continue

                    val_str = str(v).strip().upper() if v and str(v).strip() not in ("", "nan") else ""

                    if k in KOLOM_ASET_INT:
                        data_bersih[k] = 1 if val_str in ("YA", "1", "TRUE") else 0

                    elif k in ("nik", "no_kk", "nomor_kartu_keluarga"):
                        data_bersih[k] = fix_nik(v)

                    elif k.startswith("kode_"):
                        data_bersih[k] = val_str.replace(".", "") if val_str else None

                    elif k in KOLOM_INT:
                        data_bersih[k] = safe_int(v)

                    else:
                        data_bersih[k] = v if v and str(v).strip() not in ("", "nan") else None

                # Fallback untuk menyalin nama, desil_nasional, dan cut_off agar kompatibel dengan sistem
                if "desil_nasional_keluarga" in data_bersih and not data_bersih.get("desil_nasional"):
                    data_bersih["desil_nasional"] = data_bersih["desil_nasional_keluarga"]
                if "cut_off_keluarga" in data_bersih and not data_bersih.get("cut_off"):
                    data_bersih["cut_off"] = data_bersih["cut_off_keluarga"]
                if "nama_kepala_keluarga" in data_bersih and not data_bersih.get("nama"):
                    data_bersih["nama"] = data_bersih["nama_kepala_keluarga"]

                # [DITANGGUHKAN] Langkah pengisian data kosong dari default database dikomentari
                # for col_name, default_val in defaults_db.items():
                #     if col_name in data_bersih and not is_not_null(data_bersih[col_name]):
                #         if default_val is not None:
                #             data_bersih[col_name] = default_val

                # 2. Cek Idempotensi & History
                try:
                    keluarga_lama = db.query(models.Keluarga).filter(
                        models.Keluarga.no_kk == data_bersih.get("no_kk")
                    ).first()
                    print(f"DEBUG cek idempotensi untuk KK {no_kk_row}: {'Ditemukan' if keluarga_lama else 'Tidak ditemukan'}")
                except Exception as e:
                    print(f"ERROR saat cek idempotensi KK {no_kk_row}: {str(e)}")
                if keluarga_lama:
                    # Cek apakah ada perubahan variabel
                    any_changes = False
                    for k, v in data_bersih.items():
                        old_val = getattr(keluarga_lama, k, None)
                        if old_val != v:
                            any_changes = True
                            break
                    
                    if not any_changes:
                        di_skip += 1
                        log_foto.append(f"KK {no_kk_row}: DITOLAK (Duplikat, tidak ada perubahan variabel)")
                        continue

                    # Ada perubahan variabel: Arsipkan data lama
                    data_histori = {c.name: getattr(keluarga_lama, c.name) for c in models.Keluarga.__table__.columns}
                    data_histori.pop("id", None)
                    data_histori["id_keluarga"] = keluarga_lama.id

                    arsip_baru = models.KeluargaHistory(**data_histori)
                    db.add(arsip_baru)

                    for k, v in data_bersih.items():
                        setattr(keluarga_lama, k, v)
                    keluarga_diproses = keluarga_lama
                    
                    db.flush()
                else:
                    keluarga_baru = models.Keluarga(**data_bersih)
                    db.add(keluarga_baru)
                    keluarga_diproses = keluarga_baru
                    db.flush()

                # Tandai status awal sebagai "analisis" HANYA untuk data BARU
                hitung = db.query(models.Perhitungan).filter(
                    models.Perhitungan.keluarga_id == keluarga_diproses.id
                ).first()
                is_new_record = False
                if not hitung:
                    is_new_record = True
                    hitung = models.Perhitungan(
                        keluarga_id=keluarga_diproses.id,
                        user_id=current_user.id,
                        status_validasi="analisis"
                    )
                    db.add(hitung)
                else:
                    # JANGAN RESET STATUS UNTUK DATA EXISTING
                    # Hanya reset jika status masih "proses" (dari unfinished analysis)
                    if hitung.status_validasi == "proses":
                        hitung.status_validasi = "analisis"

                # 3. PROSES URL FOTO (Download ke MinIO)
                for tipe, raw_photo_urls in [("tampak_luar", raw_urls), ("tampak_dalam", raw_urls_dalam)]:
                    if not raw_photo_urls:
                        continue

                    is_tampak_dalam = (tipe == "tampak_dalam")

                    # Idempotency: cek apakah foto dengan tipe ini sudah ada untuk keluarga ini
                    foto_tipe_ada = db.query(models.Foto).filter(
                        models.Foto.keluarga_id == keluarga_diproses.id,
                        models.Foto.tampak_dalam == is_tampak_dalam
                    ).first()

                    if foto_tipe_ada:
                        log_foto.append(f"KK {no_kk_row}: SKIP foto {tipe} (sudah ada di DB)")
                        continue

                    # Bersihkan dan pecah URL
                    cleaned_urls = [u.strip(" []\"'") for u in str(raw_photo_urls).split(",") if u.strip(" []\"'")]
                    
                    for index, original_url in enumerate(cleaned_urls):
                        try:
                            foto_res = await client.get(original_url, follow_redirects=True, timeout=10.0)
                            if foto_res.status_code == 200:
                                nama_file_minio = f"{keluarga_diproses.id}_{tipe}_{index}.jpg"
                                s3_client.put_object(
                                    Bucket=MINIO_BUCKET,
                                    Key=nama_file_minio,
                                    Body=foto_res.content,
                                    ContentType="image/jpeg"
                                )
                                url_minio_final = f"http://{MINIO_PUBLIC_ENDPOINT}/{MINIO_BUCKET}/{nama_file_minio}"
                                db.add(models.Foto(
                                    keluarga_id=keluarga_diproses.id,
                                    url_foto=url_minio_final,
                                    sumber="dataset_csv",
                                    nama_file_asli=original_url,
                                    tampak_dalam=(tipe == "tampak_dalam")
                                ))
                                log_foto.append(f"KK {no_kk_row}: BERHASIL upload foto {tipe}")
                            else:
                                log_foto.append(f"KK {no_kk_row}: Gagal download foto {tipe} (HTTP {foto_res.status_code})")
                        except Exception as e:
                            log_foto.append(f"KK {no_kk_row}: ERROR foto {tipe} → {str(e)}")

                sukses += 1
                if is_new_record:
                    keluarga_ids_for_tasks.add(keluarga_diproses.id)

            except Exception as e:
                print(f"[ERROR] Baris {idx_row + 1} dengan KK {raw_row.get('nomor_kartu_keluarga', '?')} gagal diproses: {str(e)}")
                db.rollback()
                di_skip += 1
                log_foto.append(f"Error fatal baris KK {raw_row.get('nomor_kartu_keluarga', '?')}: {str(e)}")
                continue

    db.commit()

    for keluarga_id in keluarga_ids_for_tasks:
        background_tasks.add_task(run_async_visual_validation, keluarga_id, current_user.id)
        # Menghapus auto run_async_assessment agar tidak lompat ke tahap validasi otomatis

    return {
        "status": "Sukses",
        "pesan": f"{sukses} data keluarga berhasil disinkronisasi, {di_skip} baris dilewati.",
        "log_proses_foto": log_foto
    }


# ENDPOINT MANAJEMEN BANTUAN (FRONTEND)
@router.get(
    "/manajemen-bantuan",
    summary="Ambil data gabungan Keluarga dan Perhitungan AI untuk tabel Manajemen Bantuan",
)
async def get_manajemen_bantuan(
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    tahap: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    kecamatan: Optional[str] = Query(None),
    kelurahan_desa: Optional[str] = Query(None),
    desils: Optional[str] = Query(None),
    overlap: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(
        f"[GET MANAJEMEN BANTUAN] Request parameters: page={page}, limit={limit}, "
        f"tahap={tahap}, search='{search}', kecamatan={kecamatan}, "
        f"kelurahan_desa={kelurahan_desa}, desils={desils}, overlap={overlap}"
    )
    query = db.query(models.Keluarga, models.Perhitungan).outerjoin(
        models.Perhitungan, models.Perhitungan.keluarga_id == models.Keluarga.id
    ).filter(or_(
        models.Perhitungan.id.is_(None),
        models.Perhitungan.rekomendasi_bantuan.is_(None),
        func.jsonb_array_length(models.Perhitungan.rekomendasi_bantuan) > 0
    ))

    if tahap and tahap != "semua":
        if tahap == "analisis":
            query = query.filter(or_(
                models.Perhitungan.status_validasi == "analisis",
                models.Perhitungan.status_validasi.is_(None)
            ))
        else:
            query = query.filter(models.Perhitungan.status_validasi == tahap)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(or_(
            models.Keluarga.nama.ilike(search_term),
            models.Keluarga.nama_kepala_keluarga.ilike(search_term),
            models.Keluarga.nik.ilike(search_term),
            models.Keluarga.no_kk.ilike(search_term)
        ))

    if kecamatan and kecamatan != "Semua":
        query = query.filter(models.Keluarga.kecamatan == kecamatan)

    if kelurahan_desa and kelurahan_desa != "Semua":
        query = query.filter(models.Keluarga.kelurahan_desa == kelurahan_desa)

    if desils:
        desil_values = [safe_int(value) for value in desils.split(",")]
        desil_values = [value for value in desil_values if value is not None]
        if desil_values:
            query = query.filter(models.Keluarga.desil_nasional.in_(desil_values))

    if overlap and overlap != "Semua":
        if overlap == "HanyaPKHPlus":
            query = query.filter(
                models.Perhitungan.rekomendasi_bantuan.contains(["PKHT"]),
                ~models.Perhitungan.rekomendasi_bantuan.contains(["ASPD"])
            )
        elif overlap == "HanyaASPD":
            query = query.filter(
                models.Perhitungan.rekomendasi_bantuan.contains(["ASPD"]),
                ~models.Perhitungan.rekomendasi_bantuan.contains(["PKHT"])
            )
        elif overlap == "Keduanya":
            query = query.filter(
                models.Perhitungan.rekomendasi_bantuan.contains(["ASPD"]),
                models.Perhitungan.rekomendasi_bantuan.contains(["PKHT"])
            )
        elif overlap == "BelumMenerima":
            query = query.filter(or_(
                models.Perhitungan.rekomendasi_bantuan.is_(None),
                models.Perhitungan.rekomendasi_bantuan == []
            ))

    # Pastikan hasil selalu diurutkan secara konsisten berdasarkan ID atau atribut lain 
    # agar urutan data di frontend tidak berubah saat ada data yang diupdate.
    query = query.order_by(models.Keluarga.id.asc())

    total = query.count()
    paginated = page is not None or limit is not None
    page_value = page or 1
    limit_value = limit or 10

    query = query.order_by(models.Keluarga.id.asc())
    if paginated:
        query = query.offset((page_value - 1) * limit_value).limit(limit_value)

    results = query.all()
    print(f"[DEBUG] Jumlah keluarga yang di-query untuk manajemen bantuan: {len(results)}")
    response_data = []
    for k, p in results:
        tahap_ui = p.status_validasi if p and p.status_validasi else "analisis"
        rekomendasi_list = p.rekomendasi_bantuan if p and p.rekomendasi_bantuan else []
        bantuan_list = rekomendasi_list if tahap_ui in ("analisis", "validasi", "diterima", "ditolak") else []
        desil_val = k.desil_nasional or k.desil_nasional_keluarga or k.desil_nasional_anggota or 0
        row = item_schema.ManajemenBantuanResponse(
            id_keluarga=str(k.id),
            idLabel=f"ANL-{str(k.id)[:5].upper()}",
            tanggal=datetime.now().strftime("%d %b %Y"),
            nama=k.nama or "-",
            nik=k.nik or k.no_kk or "-",
            wilayah="-",
            kecamatan="-",
            desil=desil_val,
            skorASPD=p.skor_aspd if p and p.skor_aspd is not None else 0.0,
            skorPKHPlus=p.skor_pkh_plus if p and p.skor_pkh_plus else 0.0,
            tahap=tahap_ui,
            bantuan=bantuan_list,
            rekomendasiBantuan=rekomendasi_list,
            skorKesejahteraan=100.0 - (p.skor_aspd if p and p.skor_aspd is not None else 0.0),
            aiReasoning=p.reasoning_tim3 if p and p.reasoning_tim3 else "Data reasoning belum tersedia dari AI.",
            
            # Mapping variabel dinamis dari database keluarga
            kelurahan_desa=k.kelurahan_desa,
            jumlah_anggota_keluarga=k.jumlah_anggota_keluarga,
            luas_lantai_bangunan=k.luas_lantai_bangunan,
            id_lantai_terluas=k.id_lantai_terluas,
            id_dinding_terluas=k.id_dinding_terluas,
            id_atap_terluas=k.id_atap_terluas,
            id_sumber_airminum=k.id_sumber_airminum,
            id_sumberpenerangan=k.id_sumberpenerangan,
            id_bb_utama=k.id_bb_utama,
            id_fasilitas_bab=k.id_fasilitas_bab,
            id_jenis_kloset=k.id_jenis_kloset,
            id_pembuangan_tinja=k.id_pembuangan_tinja,
            id_disabilitas=k.id_disabilitas,
            tingkat_disabilitas=k.tingkat_disabilitas,
            pbi=k.pbi,
            kpm_jawara=k.kpm_jawara,
            putri_jawara=k.putri_jawara,
            aspd=k.aspd,
            eks_ppks_jawara=k.eks_ppks_jawara,
            ppks_jawara=k.ppks_jawara,
            kemiskinan_ekstrem=k.kemiskinan_ekstrem,
            pkh_plus=k.pkh_plus,
            aset_bergerak_tabung_gas=k.aset_bergerak_tabung_gas,
            aset_bergerak_lemari_es=k.aset_bergerak_lemari_es,
            aset_bergerak_ac=k.aset_bergerak_ac,
            aset_bergerak_pemanas_air=k.aset_bergerak_pemanas_air,
            aset_bergerak_telepon_rumah=k.aset_bergerak_telepon_rumah,
            aset_bergerak_tv_datar=k.aset_bergerak_tv_datar,
            aset_bergerak_emas_perhiasan=k.aset_bergerak_emas_perhiasan,
            aset_bergerak_komputer_laptop_tablet=k.aset_bergerak_komputer_laptop_tablet,
            aset_bergerak_sepeda_motor=k.aset_bergerak_sepeda_motor,
            aset_bergerak_sepeda=k.aset_bergerak_sepeda,
            aset_bergerak_mobil=k.aset_bergerak_mobil,
            aset_bergerak_perahu=k.aset_bergerak_perahu,
            aset_bergerak_kapal_perahu_motor=k.aset_bergerak_kapal_perahu_motor,
            aset_bergerak_smartphone=k.aset_bergerak_smartphone
        )
        response_data.append(row)

    if not paginated:
        return response_data

    raw_counts = db.query(
        func.coalesce(models.Perhitungan.status_validasi, "analisis"),
        func.count(models.Keluarga.id)
    ).outerjoin(
        models.Perhitungan, models.Perhitungan.keluarga_id == models.Keluarga.id
    ).filter(or_(
        models.Perhitungan.id.is_(None),
        models.Perhitungan.rekomendasi_bantuan.is_(None),
        func.jsonb_array_length(models.Perhitungan.rekomendasi_bantuan) > 0
    )).group_by(func.coalesce(models.Perhitungan.status_validasi, "analisis")).all()
    counts = {
        "semua": sum(count for _, count in raw_counts),
        "proses": 0,
        "analisis": 0,
        "validasi": 0,
        "diterima": 0,
        "ditolak": 0,
    }
    for status, count in raw_counts:
        if status in counts:
            counts[status] = count

    return item_schema.ManajemenBantuanPaginatedResponse(
        data=response_data,
        meta=item_schema.ManajemenBantuanPaginationMeta(
            page=page_value,
            limit=limit_value,
            total=total,
            totalPages=max(1, (total + limit_value - 1) // limit_value),
            counts=counts,
        )
    )

@router.get(
    "/manajemen-bantuan/{id_keluarga}",
    response_model=item_schema.DetailKeluargaResponse,
    summary="Ambil detail lengkap satu keluarga untuk halaman DetailHasil"
)
async def get_detail_manajemen_bantuan(
    id_keluarga: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    k = db.query(models.Keluarga).filter(models.Keluarga.id == id_keluarga).first()
    if not k:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")
        
    p = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == id_keluarga).first()
    f = db.query(models.Foto).filter(models.Foto.keluarga_id == id_keluarga).order_by(models.Foto.diunggah_pada.desc()).first()
    fotos = db.query(models.Foto).filter(models.Foto.keluarga_id == id_keluarga).order_by(models.Foto.diunggah_pada.asc()).all()

    if p and p.status_validasi == "proses":
        raise HTTPException(status_code=409, detail="Data masih diproses, silakan coba lagi.")
    
    tahap_ui = p.status_validasi if p and p.status_validasi else "analisis"
    rekomendasi_list = p.rekomendasi_bantuan if p and p.rekomendasi_bantuan else []
    bantuan_list = rekomendasi_list
    
    return item_schema.DetailKeluargaResponse(
        id_keluarga=str(k.id),
        idLabel=f"ANL-{str(k.id)[:5].upper()}",
        tanggal=datetime.now().strftime("%d %b %Y"),
        nama=k.nama or "-",
        nik=k.nik or k.no_kk or "-",
        wilayah="-",
        kecamatan="-",
        desil=(k.desil_nasional or k.desil_nasional_keluarga or k.desil_nasional_anggota or 0),
        skorASPD=p.skor_aspd if p and p.skor_aspd is not None else 0.0,
        skorPKHPlus=p.skor_pkh_plus if p and p.skor_pkh_plus else 0.0,
        tahap=tahap_ui,
        bantuan=bantuan_list,
        rekomendasiBantuan=rekomendasi_list,
        skorKesejahteraan=100.0 - (p.skor_aspd if p and p.skor_aspd is not None else 0.0),
        atap=k.id_atap_terluas or 0,
        dinding=k.id_dinding_terluas or 0,
        lantai=k.id_lantai_terluas or 0,
        url_foto=to_public_foto_url(f.url_foto) if f else None,
        foto_urls=[to_public_foto_url(foto.url_foto) for foto in fotos if foto.url_foto],
        visual_match=not p.ada_ketidaksesuaian_visual if p and p.ada_ketidaksesuaian_visual is not None else None,
        visual_reasoning=p.reasoning_tim2 if p else None,
        catatan=p.catatan_petugas if p else None,
        catatan_supervisor=p.catatan_supervisor if p else None,
        aiReasoning=p.reasoning_tim3 if p and p.reasoning_tim3 else "Data reasoning belum tersedia dari AI."
    )

@router.put(
    "/manajemen-bantuan/{id_keluarga}/status",
    summary="Update status validasi dan rekomendasi bantuan",
    response_model=item_schema.DetailKeluargaResponse
)
async def update_status_validasi(
    id_keluarga: UUID,
    request: item_schema.UpdateStatusValidasiRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == id_keluarga).first()
    if not p:
        p = models.Perhitungan(keluarga_id=id_keluarga)
        db.add(p)
    
    old_status = p.status_validasi if p else None
    logger.info(
        f"[UPDATE STATUS VALIDASI] ID Keluarga: {id_keluarga}. "
        f"Old Status: {old_status}, Requested New Status: {request.status_validasi}, "
        f"Bantuan: {request.bantuan}, Catatan Petugas: {request.catatan}, Catatan Supervisor: {request.catatan_supervisor}"
    )
    
    if request.status_validasi:
        p.status_validasi = request.status_validasi
        
    if request.bantuan is not None:
        p.rekomendasi_bantuan = request.bantuan
        
    if request.catatan is not None:
        p.catatan_petugas = request.catatan
        
    if request.catatan_supervisor is not None:
        p.catatan_supervisor = request.catatan_supervisor
        
    db.commit()
    logger.info(f"[UPDATE STATUS VALIDASI] Data berhasil disimpan ke database. Status akhir: {p.status_validasi}")
    
    # Trigger re-analysis tasks if transitioning to "analisis" from diterima/ditolak/validasi
    if request.status_validasi == "analisis" and old_status in ("diterima", "ditolak", "validasi"):
        logger.info(f"[UPDATE STATUS VALIDASI] Memicu re-analysis visual async untuk ID Keluarga: {id_keluarga}")
        background_tasks.add_task(run_async_visual_validation, id_keluarga, current_user.id)
    
    return await get_detail_manajemen_bantuan(id_keluarga, current_user, db)

# ENDPOINT READ DATA (GET)
@router.get(
    "/keluarga",
    summary="Ambil daftar semua keluarga (dengan pagination)"
)
async def list_keluarga(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    total = db.query(models.Keluarga).count()
    data = db.query(models.Keluarga).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [item_schema.KeluargaResponse.from_orm(k) for k in data]
    }

@router.get(
    "/keluarga/{keluarga_id}",
    summary="Ambil detail satu keluarga berdasarkan ID"
)
async def get_keluarga(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Keluarga tidak ditemukan")

    foto_terbaru = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id
    ).order_by(models.Foto.diunggah_pada.desc()).first()
    
    url_public = foto_terbaru.url_foto if foto_terbaru else None

    return item_schema.KeluargaResponse.from_orm(keluarga)

@router.get(
    "/keluarga/{keluarga_id}/histori",
    summary="Lihat riwayat perubahan asesmen satu keluarga"
)
async def get_histori(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logs = db.query(models.LogHistori).filter(
        models.LogHistori.keluarga_id == keluarga_id
    ).order_by(models.LogHistori.timestamp.desc()).all()

    return {
        "keluarga_id": str(keluarga_id),
        "jumlah_riwayat": len(logs),
        "riwayat": [
            {
                "timestamp": log.timestamp,
                "desil_lama": log.desil_lama,
                "desil_baru": log.desil_baru,
                "bantuan_lama": log.bantuan_lama,
                "bantuan_baru": log.bantuan_baru,
            }
            for log in logs
        ]
    }

