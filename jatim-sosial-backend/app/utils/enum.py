from enum import Enum

class BaseMapEnum(Enum):
    @classmethod
    def get_label(cls, val, default):
        for member in cls:
            if member.value[0] == val:
                return member.value[1]
        return default

class HubKepalaEnum(BaseMapEnum):
    KEPALA_KELUARGA = (1, "Kepala keluarga")
    ISTRI_SUAMI = (2, "Istri/suami")
    ANAK = (3, "Anak")
    MENANTU = (4, "Menantu")
    CUCU = (5, "Cucu")
    ORANGTUA_MERTUA = (6, "Orangtua/mertua")
    PEMBANTU_SOPIR = (7, "Pembantu/sopir")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Lainnya")

class StatusPerkawinanEnum(BaseMapEnum):
    BELUM_KAWIN = (1, "Belum kawin")
    KAWIN = (2, "Kawin")
    CERAI_HIDUP = (3, "Cerai hidup")
    CERAI_MATI = (4, "Cerai mati")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak diketahui")

class KondisiGiziEnum(BaseMapEnum):
    KURANG_GIZI = (1, "Kurang Gizi(Wasting)")
    KERDIL = (2, "Kerdil(Stunting)")
    TIDAK_ADA_CATATAN = (3, "Tidak ada catatan")
    TIDAK_DIKETAHUI = (8, "Tidak diketahui")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak diketahui")

class PenyakitMenahunEnum(BaseMapEnum):
    TIDAK_ADA = (1, "Tidak ada")
    HIPERTENSI = (2, "Hipertensi (darah tinggi)")
    REMATIK = (3, "Rematik")
    ASMA = (4, "Asma")
    JANTUNG = (5, "Masalah jantung")
    DIABETES = (6, "Diabetes (kencing manis)")
    TBC = (7, "Tuberkulosis (TBC)")
    STROKE = (8, "Stroke")
    KANKER_TUMOR = (9, "Kanker atau tumor ganas")
    GAGAL_GINJAL = (10, "Gagal ginjal")
    HEAMOPHILIA = (11, "Heamophilia")
    HIV_AIDS = (12, "HIV/AIDS")
    KOLESTEROL_TINGGI = (13, "Kolesterol tinggi")
    SIROSIS_HATI = (14, "Sirosis hati")
    THALASEMIA = (15, "Thalasemia")
    LEUKIMIA = (16, "Leukimia")
    ALZHEIMER = (17, "Alzheimer")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak diketahui")

class HambatanFungsiEnum(BaseMapEnum):
    TIDAK_BISA = (1, "Ya, sama sekali tidak bisa")
    BANYAK_KESULITAN = (2, "Ya, banyak kesulitan dan membutuhkan bantuan")
    SEDIKIT_KESULITAN = (3, "Ya, sedikit kesulitan, tapi tidak membutuhkan bantuan")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak mengalami kesulitan")

class StatusKeberadaanEnum(BaseMapEnum):
    DITEMUKAN_AKTIF = (1, "Ditemukan / Aktif")
    PINDAH = (2, "Pindah")
    MENINGGAL_DUNIA = (3, "Meninggal Dunia")
    TIDAK_DITEMUKAN = (4, "Tidak Ditemukan")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak Diketahui")

# -------------------------------------------------------------
# CONTOH PENGGUNAAN / MAPPING STANDAR DICTIONARY (OPTIONAL)
# -------------------------------------------------------------
# val_hub_kepala = HubKepalaEnum.label(1)  => "Kepala keluarga"
# val_hambatan = HambatanFungsiEnum.label(99) => "Tidak mengalami kesulitan" (default fallback)