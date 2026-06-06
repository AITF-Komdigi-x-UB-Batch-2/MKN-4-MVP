from app.utils.normalizer import to_int

def hitung_skor_bantuan(row: dict) -> dict:
    skor_pkh_plus = 0.0
    skor_aspd = 0.0

    desil = to_int(row.get("desil_nasional", 10), 10)
    if desil in (1, 2):
        skor_pkh_plus += 40.0
    elif desil in (3, 4):
        skor_pkh_plus += 20.0

    lantai = to_int(row.get("id_lantai_terluas", 0), 0)
    if lantai in (7, 8):
        skor_pkh_plus += 20.0

    atap = to_int(row.get("id_atap_terluas", 0), 0)
    if atap in (5, 7):
        skor_pkh_plus += 15.0

    motor = to_int(row.get("aset_bergerak_sepeda_motor", 2), 2)
    if motor == 1:
        skor_pkh_plus -= 15.0

    kolom_disabilitas = [
        "id_penglihatan", "id_pendengaran", "id_berjalan_atau_naik_tangga",
        "id_menggunakan_tangan_jari", "id_belajar_kemampuan_intelektual",
        "id_pengendalian_perilaku", "id_berbicara_komunikasi",
        "id_mengurus_diri", "id_mengingat_berkonsentrasi", "id_kesedihan_depresi"
    ]

    kondisi_terberat = 4
    for col in kolom_disabilitas:
        nilai = to_int(row.get(col, 4), 4)
        if 0 < nilai < kondisi_terberat:
            kondisi_terberat = nilai

    id_disab = to_int(row.get("id_disabilitas", 0), 0)
    if id_disab > 0:
        if kondisi_terberat == 1:
            skor_aspd += 95.0
        elif kondisi_terberat == 2:
            skor_aspd += 70.0
        elif kondisi_terberat == 3:
            skor_aspd += 30.0
    else:
        skor_aspd = 0.0

    return {
        "skor_pkh_plus": max(0.0, min(100.0, float(skor_pkh_plus))),
        "skor_aspd": max(0.0, min(100.0, float(skor_aspd)))
    }
