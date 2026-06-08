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
    
class LantaiEnum(BaseMapEnum):
    MARMER_GRANIT = (1, "Marmer/granit")
    KERAMIK = (2, "Keramik")
    PARKET_VINIL_KARPET = (3, "Parket/vinil/karpet")
    UBIN_TEGEL_TERASO = (4, "Ubin/tegel/teraso")
    KAYU_PAPAN = (5, "Kayu/papan")
    SEMEN_BATA_MERAH = (6, "Semen/bata merah")
    BAMBU = (7, "Bambu")
    TANAH = (8, "Tanah")
    LAINNYA = (9, "Lainnya")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak terdeteksi")

class AtapEnum(BaseMapEnum):
    BETON = (1, "Beton")
    GENTENG = (2, "Genteng")
    SENG = (3, "Seng")
    ASBES = (4, "Asbes")
    BAMBU = (5, "Bambu")
    KAYU_SIRAP = (6, "Kayu/sirap")
    JERAMI_RUMBIA = (7, "Jerami/ijuk/daun-daunan/rumbia")
    LAINNYA = (8, "Lainnya")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak terdeteksi")

class DindingEnum(BaseMapEnum):
    TEMBOK = (1, "Tembok")
    PLESTERAN_BAMBU = (2, "Plesteran anyaman bambu/kawat")
    KAYU_PAPAN_GRC = (3, "Kayu/papan/gypsum/GRC/calciboard")
    ANYAMAN_BAMBU = (4, "Anyaman bambu")
    BATANG_KAYU = (5, "Batang kayu")
    BAMBU = (6, "Bambu")
    LAINNYA = (7, "Lainnya")
    
    @classmethod
    def label(cls, val):
        return cls.get_label(val, default="Tidak terdeteksi")


# -------------------------------------------------------------
# CONTOH PENGGUNAAN / MAPPING STANDAR DICTIONARY (OPTIONAL)
# -------------------------------------------------------------
# val_hub_kepala = HubKepalaEnum.label(1)  => "Kepala keluarga"
# val_hambatan = HambatanFungsiEnum.label(99) => "Tidak mengalami kesulitan" (default fallback)