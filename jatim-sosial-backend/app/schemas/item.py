from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Schema untuk response
class KeluargaResponse(BaseModel):
    id: UUID
    nama: Optional[str] = None
    no_kk: str
    nik: Optional[str] = None
    tanggal_lahir: Optional[str] = None
    umur_2026: Optional[int] = None
    pkh_plus: Optional[int] = None
    desil_nasional_anggota: Optional[int] = None
    desil_nasional_keluarga: Optional[int] = None
    bansos: Optional[str] = None
    kemiskinan_ekstrem: Optional[int] = None
    tempat_lahir: Optional[str] = None
    id_jenis_kelamin: Optional[int] = None
    id_hub_kepala_keluarga: Optional[int] = None
    id_disabilitas: Optional[int] = None
    tingkat_disabilitas: Optional[str] = None
    pbi: Optional[int] = None
    id_status_perkawinan: Optional[int] = None
    id_partisipasi_sekolah: Optional[int] = None
    id_jenjang_pendidikan_dukcapil: Optional[int] = None
    membantu_bekerja: Optional[int] = None
    id_lapangan_usaha_dari_usaha_utama: Optional[int] = None
    id_status_kedudukan_pekerjaan_utama: Optional[int] = None
    id_kepemilikan_izin_usaha: Optional[int] = None
    jumlah_jenis_usaha: Optional[int] = None
    id_pekerjaan_utama: Optional[int] = None
    jumlah_pekerja_dibayar: Optional[int] = None
    jumlah_pekerja_tidak_dibayar: Optional[int] = None
    id_omset_usaha_utama: Optional[int] = None
    id_kondisi_gizi: Optional[int] = None
    id_penglihatan: Optional[int] = None
    id_pendengaran: Optional[int] = None
    id_berjalan_atau_naik_tangga: Optional[int] = None
    id_menggunakan_tangan_jari: Optional[int] = None
    id_belajar_kemampuan_intelektual: Optional[int] = None
    id_pengendalian_perilaku: Optional[int] = None
    id_berbicara_komunikasi: Optional[int] = None
    id_mengurus_diri: Optional[int] = None
    id_mengingat_berkonsentrasi: Optional[int] = None
    id_kesedihan_depresi: Optional[int] = None
    id_penyakit_menahun: Optional[int] = None
    status_dtsen: Optional[str] = None
    kpm_jawara: Optional[int] = None
    putri_jawara: Optional[int] = None
    aspd: Optional[int] = None
    eks_ppks_jawara: Optional[int] = None
    ppks_jawara: Optional[int] = None
    kode_provinsi: Optional[str] = None
    id_status_keberadaan_keluarga: Optional[int] = None
    id_dayapenerangan: Optional[int] = None
    jumlah_anggota_keluarga: Optional[int] = None
    id_status_penguasaan_bangunan: Optional[int] = None
    id_lantai_terluas: Optional[int] = None
    luas_lantai_bangunan: Optional[int] = None
    id_dinding_terluas: Optional[int] = None
    id_atap_terluas: Optional[int] = None
    id_sumber_airminum: Optional[int] = None
    id_sumberpenerangan: Optional[int] = None
    id_bb_utama: Optional[int] = None
    id_fasilitas_bab: Optional[int] = None
    id_jenis_kloset: Optional[int] = None
    id_pembuangan_tinja: Optional[int] = None
    kepemilikan_aset: Optional[int] = None
    aset_bergerak_tabung_gas: Optional[int] = None
    aset_bergerak_lemari_es: Optional[int] = None
    aset_bergerak_ac: Optional[int] = None
    aset_bergerak_pemanas_air: Optional[int] = None
    aset_bergerak_telepon_rumah: Optional[int] = None
    aset_bergerak_tv_datar: Optional[int] = None
    aset_bergerak_emas_perhiasan: Optional[int] = None
    aset_bergerak_komputer_laptop_tablet: Optional[int] = None
    aset_bergerak_sepeda_motor: Optional[int] = None
    aset_bergerak_sepeda: Optional[int] = None
    aset_bergerak_mobil: Optional[int] = None
    aset_bergerak_perahu: Optional[int] = None
    aset_bergerak_kapal_perahu_motor: Optional[int] = None
    aset_bergerak_smartphone: Optional[int] = None
    lahan_tempat_lain: Optional[int] = None
    rumah_tempat_lain: Optional[int] = None
    jml_sapi: Optional[int] = None
    jml_kerbau: Optional[int] = None
    jml_kuda: Optional[int] = None
    jml_babi: Optional[int] = None
    jml_kambing_domba: Optional[int] = None
    cut_off_keluarga: Optional[str] = None

    class Config:
        from_attributes = True

class FotoResponse(BaseModel):
    id: UUID
    keluarga_id: UUID
    url_foto: str
    tampak_dalam: bool = False
    periode: Optional[str] = None
    sumber: Optional[str] = None
    nama_file_asli: Optional[str] = None
    diunggah_pada: datetime

    class Config:
        from_attributes = True

# Schema tabel perhitungan (hasil AI)
class PerhitunganResponse(BaseModel):
    id: UUID
    keluarga_id: UUID
    rekomendasi_bantuan: Optional[List] = None
    reasoning_tim2: Optional[str] = None
    reasoning_tim3: Optional[str] = None
    desil_kemiskinan: Optional[str] = None
    ada_ketidaksesuaian_visual: Optional[bool] = None
    status_validasi: Optional[str] = None
    catatan_petugas: Optional[str] = None

    class Config:
        from_attributes = True

# Schema request
class TriggerAsesmenRequest(BaseModel):
    keluarga_id: UUID

class UpdateStatusValidasiRequest(BaseModel):
    status_validasi: str
    bantuan: Optional[List[str]] = None
    catatan: Optional[str] = None
    catatan_supervisor: Optional[str] = None

class ManajemenBantuanResponse(BaseModel):
    id_keluarga: str
    idLabel: str
    tanggal: str
    nama: str
    nik: str
    wilayah: str
    kecamatan: str
    desil: int
    skorASPD: float
    skorPKHPlus: float
    tahap: str
    bantuan: list[str]
    rekomendasiBantuan: list[str]
    skorKesejahteraan: float
    aiReasoning: str

    # Tambahan variabel dinamis untuk Atur Kolom (Show/Hide) & Filter
    kelurahan_desa: Optional[str] = None
    jumlah_anggota_keluarga: Optional[int] = None
    luas_lantai_bangunan: Optional[int] = None
    id_lantai_terluas: Optional[int] = None
    id_dinding_terluas: Optional[int] = None
    id_atap_terluas: Optional[int] = None
    id_sumber_airminum: Optional[int] = None
    id_sumberpenerangan: Optional[int] = None
    id_bb_utama: Optional[int] = None
    id_fasilitas_bab: Optional[int] = None
    id_jenis_kloset: Optional[int] = None
    id_pembuangan_tinja: Optional[int] = None
    id_disabilitas: Optional[int] = None
    tingkat_disabilitas: Optional[str] = None
    pbi: Optional[int] = None
    kpm_jawara: Optional[int] = None
    putri_jawara: Optional[int] = None
    aspd: Optional[int] = None
    eks_ppks_jawara: Optional[int] = None
    ppks_jawara: Optional[int] = None
    kemiskinan_ekstrem: Optional[int] = None
    pkh_plus: Optional[int] = None
    aset_bergerak_tabung_gas: Optional[int] = None
    aset_bergerak_lemari_es: Optional[int] = None
    aset_bergerak_ac: Optional[int] = None
    aset_bergerak_pemanas_air: Optional[int] = None
    aset_bergerak_telepon_rumah: Optional[int] = None
    aset_bergerak_tv_datar: Optional[int] = None
    aset_bergerak_emas_perhiasan: Optional[int] = None
    aset_bergerak_komputer_laptop_tablet: Optional[int] = None
    aset_bergerak_sepeda_motor: Optional[int] = None
    aset_bergerak_sepeda: Optional[int] = None
    aset_bergerak_mobil: Optional[int] = None
    aset_bergerak_perahu: Optional[int] = None
    aset_bergerak_kapal_perahu_motor: Optional[int] = None
    aset_bergerak_smartphone: Optional[int] = None

    class Config:
        from_attributes = True

class ManajemenBantuanPaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int
    counts: dict[str, int]

class ManajemenBantuanPaginatedResponse(BaseModel):
    data: list[ManajemenBantuanResponse]
    meta: ManajemenBantuanPaginationMeta

class DetailKeluargaResponse(BaseModel):
    id_keluarga: str
    idLabel: str
    tanggal: str
    nama: str
    nik: str
    wilayah: str
    kecamatan: str
    desil: int
    skorKesejahteraan: float
    tahap: str
    bantuan: list[str]
    rekomendasiBantuan: list[str]
    skorASPD: float
    skorPKHPlus: float
    
    # Material
    atap: int
    dinding: int
    lantai: int

    # AI visual
    url_foto: Optional[str] = None
    foto_urls: list[str] = []
    visual_match: Optional[bool] = None
    visual_reasoning: Optional[str] = None
    catatan: Optional[str] = None
    catatan_supervisor: Optional[str] = None

    # AI Tim 3
    aiReasoning: str
