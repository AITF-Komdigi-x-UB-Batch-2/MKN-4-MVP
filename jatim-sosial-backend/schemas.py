from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Schema untuk response
class KeluargaResponse(BaseModel):
    id: UUID
    kode_provinsi: Optional[str] = None
    provinsi: Optional[str] = None
    kode_kabupaten_kota: Optional[str] = None
    kabupaten_kota: Optional[str] = None
    kode_kecamatan: Optional[str] = None
    kecamatan: Optional[str] = None
    kode_kelurahan_desa: Optional[str] = None
    kelurahan_desa: Optional[str] = None
    alamat: Optional[str] = None
    nomor_kartu_keluarga: str
    jumlah_anggota_keluarga: Optional[int] = None
    nama_anggota_keluarga: Optional[str] = None
    pbi_nas: Optional[bool] = None
    pbi_pemda: Optional[bool] = None
    id_pelanggan_pln: Optional[str] = None
    status_kepemilikan_rumah: Optional[int] = None
    jenis_lantai_terluas: Optional[int] = None
    luas_lantai: Optional[int] = None
    jenis_dinding_terluas: Optional[int] = None
    jenis_atap_terluas: Optional[int] = None
    sumber_air_minum_utama: Optional[int] = None
    sumber_penerangan_utama: Optional[int] = None
    daya_terpasang: Optional[int] = None
    bahan_bakar_utama_memasak: Optional[int] = None
    fasilitas_bab: Optional[int] = None
    jenis_kloset: Optional[int] = None
    pembuangan_akhir_tinja: Optional[int] = None
    kepemilikan_aset: Optional[bool] = None
    aset_bergerak_tabung_gas: Optional[bool] = None
    aset_bergerak_lemari_es: Optional[bool] = None
    aset_bergerak_ac: Optional[bool] = None
    aset_bergerak_pemanas_air: Optional[bool] = None
    aset_bergerak_telepon_rumah: Optional[bool] = None
    aset_bergerak_tv_datar: Optional[bool] = None
    aset_bergerak_emas_perhiasan: Optional[bool] = None
    aset_bergerak_komputer_laptop_tablet: Optional[bool] = None
    aset_bergerak_sepeda_motor: Optional[bool] = None
    aset_bergerak_sepeda: Optional[bool] = None
    aset_bergerak_mobil: Optional[bool] = None
    aset_bergerak_perahu: Optional[bool] = None
    aset_bergerak_kapal_perahu_motor: Optional[bool] = None
    aset_bergerak_smartphone: Optional[bool] = None
    aset_tidak_bergerak_lahan_lainnya: Optional[bool] = None
    aset_tidak_bergerak_rumah_lainnya: Optional[bool] = None
    jumlah_ternak_sapi: Optional[int] = None
    jumlah_ternak_kerbau: Optional[int] = None
    jumlah_ternak_kuda: Optional[int] = None
    jumlah_ternak_babi: Optional[int] = None
    jumlah_ternak_kambing_domba: Optional[int] = None
    skor: Optional[int] = None
    desil_nasional: Optional[int] = None

    class Config:
        from_attributes = True

class FotoResponse(BaseModel):
    id: UUID
    keluarga_id: UUID
    url_foto: str
    tampak_dalam: Optional[bool] = None
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
    reasoning_tim1: Optional[str] = None
    reasoning_tim3: Optional[str] = None
    desil_kemiskinan: Optional[str] = None
    skor_prioritas: Optional[int] = None
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

class UserCreate(BaseModel):
    email: str = Field(..., example="analis@dinsos.go.id")
    username: str = Field(..., example="analis_jatim")
    password: str = Field(..., example="password123")
    role: str = Field(default="ANALIS", example="ANALIS")

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    dibuat_pada: datetime

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    new_password: Optional[str] = None

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
    skorPKHT: float
    tahap: str
    bantuan: list[str]
    rekomendasiBantuan: list[str]
    skorKesejahteraan: float
    aiReasoning: str

    class Config:
        from_attributes = True

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
    skorPKHT: float
    
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