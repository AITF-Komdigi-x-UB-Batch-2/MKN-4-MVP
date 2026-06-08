"""
FILE: app/utils/enum.py
DESKRIPSI:
Kumpulan Enum untuk semua variabel berkode pada data DTSEN (Individu & Keluarga).
Sesuai LIST VARIABEL resmi.
"""

from enum import Enum


class BaseMapEnum(Enum):
    @classmethod
    def get_label(cls, val, default="Tidak diketahui"):
        for member in cls:
            if member.value[0] == val:
                return member.value[1]
        return default

    @classmethod
    def label(cls, val):
        return cls.get_label(val)

    @classmethod
    def choices(cls):
        """Kembalikan list of (value, label) untuk semua member."""
        return [(m.value[0], m.value[1]) for m in cls]


# ==============================================================
# INDIVIDU
# ==============================================================

class JenisKelaminEnum(BaseMapEnum):
    LAKI_LAKI  = (1, "Laki-laki")
    PEREMPUAN  = (2, "Perempuan")


class HubKepalaEnum(BaseMapEnum):
    KEPALA_KELUARGA = (1, "Kepala keluarga")
    ISTRI_SUAMI     = (2, "Istri/suami")
    ANAK            = (3, "Anak")
    MENANTU         = (4, "Menantu")
    CUCU            = (5, "Cucu")
    ORANGTUA_MERTUA = (6, "Orangtua/mertua")
    PEMBANTU_SOPIR  = (7, "Pembantu/sopir")
    LAINNYA         = (8, "Lainnya")


class StatusPerkawinanEnum(BaseMapEnum):
    BELUM_KAWIN = (1, "Belum kawin")
    KAWIN       = (2, "Kawin/nikah")
    CERAI_HIDUP = (3, "Cerai hidup")
    CERAI_MATI  = (4, "Cerai mati")


class PartisipasiSekolahEnum(BaseMapEnum):
    TIDAK_PERNAH_SEKOLAH = (1, "Tidak/belum pernah sekolah")
    MASIH_SEKOLAH        = (2, "Masih sekolah")
    TIDAK_BERSEKOLAH     = (3, "Tidak bersekolah lagi")


class JenjangPendidikanEnum(BaseMapEnum):
    PAKET_A       = (1,  "Paket A")
    SDLB          = (2,  "SDLB")
    SD            = (3,  "SD")
    MI            = (4,  "MI")
    SPM_PDF_ULA   = (5,  "SPM/PDF Ula")
    PAKET_B       = (6,  "Paket B")
    SMP_LB        = (7,  "SMP LB")
    SMP           = (8,  "SMP")
    MTS           = (9,  "MTs")
    SPM_PDF_WUSTHA = (10, "SPM/PDF Wustha")
    PAKET_C       = (11, "Paket C")
    SMLB          = (12, "SMLB")
    SMA           = (13, "SMA")
    MA            = (14, "MA")
    SMK           = (15, "SMK")
    MAK           = (16, "MAK")
    SPM_PDF_ULYA  = (17, "SPM/PDF Ulya")
    D1_D2_D3      = (18, "D1/D2/D3")
    D4_S1         = (19, "D4/S1")
    PROFESI       = (20, "Profesi")
    S2            = (21, "S2")
    S3            = (22, "S3")


class MembantuBekerjaEnum(BaseMapEnum):
    YA    = (1, "Ya")
    TIDAK = (2, "Tidak")


class LapanganUsahaEnum(BaseMapEnum):
    """
    Digunakan untuk: id_lapangan_usaha_dari_usaha_utama & id_pekerjaan_utama
    """
    PERTANIAN_TANAMAN_PANGAN   = (1,  "Pertanian tanaman pangan dan palawija")
    HORTIKULTURA               = (2,  "Hortikultura")
    PERKEBUNAN                 = (3,  "Perkebunan")
    PERIKANAN                  = (4,  "Perikanan")
    PETERNAKAN                 = (5,  "Peternakan")
    KEHUTANAN                  = (6,  "Kehutanan dan pertanian lainnya")
    PERTAMBANGAN               = (7,  "Pertambangan/penggalian")
    INDUSTRI_PENGOLAHAN        = (8,  "Industri pengolahan")
    LISTRIK_GAS                = (9,  "Pengadaan listrik, gas, uap/air panas, dan udara dingin")
    AIR_LIMBAH                 = (10, "Pengelolaan air, limbah, daur ulang sampah, dan remediasi")
    KONSTRUKSI                 = (11, "Konstruksi")
    PERDAGANGAN                = (12, "Perdagangan besar dan eceran, reparasi mobil dan motor")
    PENGANGKUTAN               = (13, "Pengangkutan dan pergudangan")
    AKOMODASI_MAKAN_MINUM      = (14, "Penyediaan akomodasi dan makan minum")
    INFORMASI_KOMUNIKASI       = (15, "Informasi dan komunikasi")
    KEUANGAN_ASURANSI          = (16, "Keuangan dan asuransi")
    REAL_ESTATE                = (17, "Real estate")
    PROFESIONAL_ILMIAH         = (18, "Aktivitas profesional, ilmiah, dan teknis")
    PENYEWAAN_KETENAGAKERJAAN  = (19, "Aktivitas penyewaan, ketenagakerjaan, agen perjalanan, dan usaha lainnya")
    ADMINISTRASI_PEMERINTAHAN  = (20, "Administrasi pemerintahan, pertahanan, dan jaminan sosial wajib")
    PENDIDIKAN                 = (21, "Pendidikan")
    KESEHATAN_SOSIAL           = (22, "Aktivitas kesehatan manusia dan aktivitas sosial")
    KESENIAN_HIBURAN           = (23, "Kesenian, hiburan, dan rekreasi")
    JASA_LAINNYA               = (24, "Aktivitas jasa lainnya")
    KELUARGA_PEMBERI_KERJA     = (25, "Aktivitas keluarga sebagai pemberi kerja")
    BADAN_INTERNASIONAL        = (26, "Aktivitas badan internasional dan ekstra internasional lainnya")


class StatusKedudukanPekerjaanEnum(BaseMapEnum):
    BERUSAHA_SENDIRI              = (1, "Berusaha sendiri")
    BERUSAHA_BURUH_TIDAK_TETAP    = (2, "Berusaha dibantu buruh tidak tetap/tidak dibayar")
    BERUSAHA_BURUH_TETAP          = (3, "Berusaha dibantu buruh tetap/buruh dibayar")
    BURUH_SWASTA                  = (4, "Buruh/karyawan/pegawai swasta")
    PNS_TNI_POLRI                 = (5, "PNS/TNI/Polri/BUMN/BUMD/pejabat negara")
    PEKERJA_BEBAS_PERTANIAN       = (6, "Pekerja bebas pertanian")
    PEKERJA_BEBAS_NON_PERTANIAN   = (7, "Pekerja bebas non pertanian")
    PEKERJA_KELUARGA              = (8, "Pekerja keluarga/tidak dibayar")


class KepemilikanIzinUsahaEnum(BaseMapEnum):
    YA    = (1, "Ya")
    TIDAK = (2, "Tidak")


class OmsetUsahaEnum(BaseMapEnum):
    ULTRA_MIKRO_1 = (1, "< 5 Juta (ultra mikro)")
    ULTRA_MIKRO_2 = (2, "5 - <15 Juta (ultra mikro)")
    ULTRA_MIKRO_3 = (3, "15 - <25 Juta (ultra mikro)")
    MIKRO         = (4, "25 - <167 Juta (mikro)")
    KECIL         = (5, "167 - <1.250 Juta (kecil)")
    MENENGAH      = (6, "1.250 - <4.167 Juta (menengah)")
    BESAR         = (7, "\u2265 4.167 Juta (besar)")


class KondisiGiziEnum(BaseMapEnum):
    KURANG_GIZI       = (1, "Kurang gizi (Wasting)")
    KERDIL            = (2, "Kerdil (Stunting)")
    TIDAK_ADA_CATATAN = (3, "Tidak ada catatan")
    TIDAK_TAHU        = (8, "Tidak tahu")


class HambatanFungsiEnum(BaseMapEnum):
    """
    Digunakan untuk: id_penglihatan, id_pendengaran, id_berjalan_atau_naik_tangga,
    id_menggunakan_tangan_jari, id_belajar_kemampuan_intelektual,
    id_pengendalian_perilaku, id_berbicara_komunikasi,
    id_mengurus_diri, id_mengingat_berkonsentrasi
    """
    SAMA_SEKALI_TIDAK_BISA  = (1, "Ya, sama sekali tidak bisa")
    BANYAK_KESULITAN        = (2, "Ya, banyak kesulitan dan membutuhkan bantuan")
    SEDIKIT_KESULITAN       = (3, "Ya, sedikit kesulitan, tapi tidak membutuhkan bantuan")
    TIDAK_MENGALAMI         = (4, "Tidak mengalami kesulitan")


class KesedihanDepresiEnum(BaseMapEnum):
    SANGAT_SERING = (1, "Sangat sering")
    SERING        = (2, "Sering")
    JARANG        = (3, "Jarang")
    TIDAK_PERNAH  = (4, "Tidak pernah")


class PenyakitMenahunEnum(BaseMapEnum):
    TIDAK_ADA    = (1,  "Tidak ada")
    HIPERTENSI   = (2,  "Hipertensi")
    REMATIK      = (3,  "Rematik")
    ASMA         = (4,  "Asma")
    JANTUNG      = (5,  "Masalah jantung")
    DIABETES     = (6,  "Diabetes")
    TBC          = (7,  "Tuberculosis (TBC)")
    STROKE       = (8,  "Stroke")
    KANKER_TUMOR = (9,  "Kanker atau tumor ganas")
    GAGAL_GINJAL = (10, "Gagal ginjal")
    HAEMOPHILIA  = (11, "Haemophilia")
    HIV_AIDS     = (12, "HIV/AIDS")
    KOLESTEROL   = (13, "Kolesterol")
    SIROSIS_HATI = (14, "Sirosis hati")
    THALASEMIA   = (15, "Thalasemia")
    LEUKIMIA     = (16, "Leukimia")
    ALZHEIMER    = (17, "Alzheimer")
    LAINNYA      = (18, "Lainnya")


# ==============================================================
# STATUS DTSEN
# ==============================================================

class StatusDTSENEnum(str, Enum):
    AKTIF                 = "DTSEN AKTIF"
    AKTIF_MENINGGAL       = "DTSEN AKTIF - ASESMEN MENINGGAL"
    NONAKTIF              = "DTSEN NONAKTIF"


# ==============================================================
# KELUARGA – KONDISI BANGUNAN RUMAH
# ==============================================================

class StatusPenguasaanBangunanEnum(BaseMapEnum):
    MILIK_SENDIRI  = (1, "Milik sendiri")
    KONTRAK_SEWA   = (2, "Kontrak/sewa")
    BEBAS_SEWA     = (3, "Bebas sewa")
    DINAS          = (4, "Dinas")
    LAINNYA        = (5, "Lainnya")


class LantaiTerluasEnum(BaseMapEnum):
    MARMER_GRANIT     = (1, "Marmer/granit")
    KERAMIK           = (2, "Keramik")
    PARKET_VINIL      = (3, "Parket/vinil/karpet")
    UBIN_TEGEL        = (4, "Ubin/tegel/teraso")
    KAYU_PAPAN        = (5, "Kayu/papan")
    SEMEN_BATA        = (6, "Semen/bata merah")
    BAMBU             = (7, "Bambu")
    TANAH             = (8, "Tanah")
    LAINNYA           = (9, "Lainnya")


class DindingTerluasEnum(BaseMapEnum):
    TEMBOK              = (1, "Tembok")
    PLESTERAN_BAMBU     = (2, "Plesteran anyaman bambu/kawat")
    KAYU_PAPAN_GRC      = (3, "Kayu/papan/gypsum/GRC/calciboard")
    ANYAMAN_BAMBU       = (4, "Anyaman bambu")
    BATANG_KAYU         = (5, "Batang kayu")
    BAMBU               = (6, "Bambu")
    LAINNYA             = (7, "Lainnya")


class AtapTerluasEnum(BaseMapEnum):
    BETON                = (1, "Beton")
    GENTENG              = (2, "Genteng")
    SENG                 = (3, "Seng")
    ASBES                = (4, "Asbes")
    BAMBU                = (5, "Bambu")
    KAYU_SIRAP           = (6, "Kayu/sirap")
    JERAMI_IJUK          = (7, "Jerami/ijuk/daun-daunan/rumbia")
    LAINNYA              = (8, "Lainnya")


# ==============================================================
# KELUARGA – SANITASI DAN AIR BERSIH
# ==============================================================

class SumberAirMinumEnum(BaseMapEnum):
    AIR_KEMASAN       = (1,  "Air kemasan bermerk")
    AIR_ISI_ULANG     = (2,  "Air isi ulang")
    LEDING            = (3,  "Leding")
    SUMUR_BOR         = (4,  "Sumur bor/pompa")
    SUMUR_TERLINDUNG  = (5,  "Sumur terlindung")
    SUMUR_TAK_LINDUNG = (6,  "Sumur tak terlindung")
    MATA_AIR_LINDUNG  = (7,  "Mata air terlindung")
    MATA_AIR_TAK      = (8,  "Mata air tak terlindung")
    AIR_PERMUKAAN     = (9,  "Air permukaan (sungai/danau/waduk/kolam/irigasi)")
    AIR_HUJAN         = (10, "Air hujan")
    LAINNYA           = (11, "Lainnya")


class FasilitasBABEnum(BaseMapEnum):
    SENDIRI          = (1, "Ada, digunakan hanya anggota keluarga sendiri")
    BERSAMA_TERTENTU = (2, "Ada, digunakan bersama anggota keluarga dari keluarga tertentu")
    MCK_KOMUNAL      = (3, "Ada, di MCK komunal")
    MCK_UMUM         = (4, "Ada, di MCK umum/siapapun menggunakan")
    TIDAK_DIGUNAKAN  = (5, "Ada, anggota keluarga tidak menggunakan")
    TIDAK_ADA        = (6, "Tidak ada fasilitas")


class JenisKlosetEnum(BaseMapEnum):
    LEHER_ANGSA            = (1, "Leher angsa")
    PLENGSENGAN_TUTUP      = (2, "Plengsengan dengan tutup")
    PLENGSENGAN_TANPA      = (3, "Plengsengan tanpa tutup")
    CEMPLUNG               = (4, "Cemplung/cubluk")


class PembuanganTinjaEnum(BaseMapEnum):
    TANGKI_SEPTIK    = (1, "Tangki septik")
    IPAL             = (2, "IPAL")
    SUNGAI_KOLAM     = (3, "Kolam/sawah/sungai/danau/laut")
    LUBANG_TANAH     = (4, "Lubang tanah")
    PANTAI_KEBUN     = (5, "Pantai/tanah lapang/kebun")
    LAINNYA          = (6, "Lainnya")


# ==============================================================
# KELUARGA – ENERGI DAN UTILITAS
# ==============================================================

class SumberPeneranganEnum(BaseMapEnum):
    PLN_METERAN     = (1, "Listrik PLN dengan meteran")
    PLN_TANPA_METER = (2, "Listrik PLN tanpa meteran")
    NON_PLN         = (3, "Listrik non-PLN")
    BUKAN_LISTRIK   = (4, "Bukan listrik")


class BBUtamaEnum(BaseMapEnum):
    TIDAK_MEMASAK   = (0,  "Tidak memasak di rumah")
    LISTRIK         = (1,  "Listrik")
    GAS_55_BLUE     = (2,  "Gas elpiji 5,5 kg/blue gaz")
    GAS_12          = (3,  "Gas elpiji 12 kg")
    GAS_3           = (4,  "Gas elpiji 3 kg")
    GAS_KOTA        = (5,  "Gas kota/meteran PGN")
    BIOGAS          = (6,  "Biogas")
    MINYAK_TANAH    = (7,  "Minyak tanah")
    BRIKET          = (8,  "Briket")
    ARANG           = (9,  "Arang")
    KAYU_BAKAR      = (10, "Kayu bakar")
    LAINNYA         = (11, "Lainnya")


# ==============================================================
# STATUS KEBERADAAN (internal asesmen)
# ==============================================================

class StatusKeberadaanEnum(BaseMapEnum):
<<<<<<< HEAD
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

=======
    DITEMUKAN_AKTIF  = (1, "Ditemukan / Aktif")
    PINDAH           = (2, "Pindah")
    MENINGGAL_DUNIA  = (3, "Meninggal Dunia")
    TIDAK_DITEMUKAN  = (4, "Tidak Ditemukan")
>>>>>>> db349eed84338baf3fd3989d1e6105a7a0e88b34


# ==============================================================
# CONTOH PENGGUNAAN
# ==============================================================
# HubKepalaEnum.label(1)            => "Kepala keluarga"
# HambatanFungsiEnum.label(4)       => "Tidak mengalami kesulitan"
# PenyakitMenahunEnum.label(18)     => "Lainnya"
# LapanganUsahaEnum.label(12)       => "Perdagangan besar dan eceran, reparasi mobil dan motor"
# BBUtamaEnum.label(4)              => "Gas elpiji 3 kg"
# HambatanFungsiEnum.choices()      => [(1,"Ya, sama sekali tidak bisa"), ...]