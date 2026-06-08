import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AdminLayout from "../../components/layout/AdminLayout";
import {
  MapPin,
  FileText,
  Home,
  Monitor,
  Leaf,
  ShieldCheck,
  Loader2,
  ArrowLeft,
  Briefcase,
  Heart,
} from "lucide-react";
import { getKeluargaDetail, type KeluargaDetail } from "../../services/api";
import "./DetailKeluarga.css";

interface DetailKeluargaProps {
  onLogout?: () => void;
}

// ── Label lookup maps (sesuai enum.py) ────────────────────────────────────────
const LABEL_JENIS_KELAMIN: Record<number, string> = { 1: "Laki-laki", 2: "Perempuan" };
const LABEL_STATUS_PERKAWINAN: Record<number, string> = { 1: "Belum kawin", 2: "Kawin/nikah", 3: "Cerai hidup", 4: "Cerai mati" };
const LABEL_PARTISIPASI_SEKOLAH: Record<number, string> = { 1: "Tidak/belum pernah sekolah", 2: "Masih sekolah", 3: "Tidak bersekolah lagi" };
const LABEL_JENJANG: Record<number, string> = {
  1: "Paket A", 2: "SDLB", 3: "SD", 4: "MI", 5: "SPM/PDF Ula",
  6: "Paket B", 7: "SMP LB", 8: "SMP", 9: "MTs", 10: "SPM/PDF Wustha",
  11: "Paket C", 12: "SMLB", 13: "SMA", 14: "MA", 15: "SMK",
  16: "MAK", 17: "SPM/PDF Ulya", 18: "D1/D2/D3", 19: "D4/S1",
  20: "Profesi", 21: "S2", 22: "S3",
};
const LABEL_LAPANGAN_USAHA: Record<number, string> = {
  1: "Pertanian tanaman pangan dan palawija", 2: "Hortikultura", 3: "Perkebunan",
  4: "Perikanan", 5: "Peternakan", 6: "Kehutanan dan pertanian lainnya",
  7: "Pertambangan/penggalian", 8: "Industri pengolahan",
  9: "Pengadaan listrik, gas, uap/air panas, dan udara dingin",
  10: "Pengelolaan air, limbah, daur ulang sampah, dan remediasi",
  11: "Konstruksi", 12: "Perdagangan besar dan eceran, reparasi mobil dan motor",
  13: "Pengangkutan dan pergudangan", 14: "Penyediaan akomodasi dan makan minum",
  15: "Informasi dan komunikasi", 16: "Keuangan dan asuransi", 17: "Real estate",
  18: "Aktivitas profesional, ilmiah, dan teknis",
  19: "Aktivitas penyewaan, ketenagakerjaan, agen perjalanan, dan usaha lainnya",
  20: "Administrasi pemerintahan, pertahanan, dan jaminan sosial wajib",
  21: "Pendidikan", 22: "Aktivitas kesehatan manusia dan aktivitas sosial",
  23: "Kesenian, hiburan, dan rekreasi", 24: "Aktivitas jasa lainnya",
  25: "Aktivitas keluarga sebagai pemberi kerja",
  26: "Aktivitas badan internasional dan ekstra internasional lainnya",
};
const LABEL_STATUS_KEDUDUKAN: Record<number, string> = {
  1: "Berusaha sendiri", 2: "Berusaha dibantu buruh tidak tetap/tidak dibayar",
  3: "Berusaha dibantu buruh tetap/buruh dibayar", 4: "Buruh/karyawan/pegawai swasta",
  5: "PNS/TNI/Polri/BUMN/BUMD/pejabat negara", 6: "Pekerja bebas pertanian",
  7: "Pekerja bebas non pertanian", 8: "Pekerja keluarga/tidak dibayar",
};
const LABEL_OMSET: Record<number, string> = {
  1: "< 5 Juta (ultra mikro)", 2: "5 - <15 Juta (ultra mikro)", 3: "15 - <25 Juta (ultra mikro)",
  4: "25 - <167 Juta (mikro)", 5: "167 - <1.250 Juta (kecil)",
  6: "1.250 - <4.167 Juta (menengah)", 7: "≥ 4.167 Juta (besar)",
};
const LABEL_KONDISI_GIZI: Record<number, string> = { 1: "Kurang gizi (Wasting)", 2: "Kerdil (Stunting)", 3: "Tidak ada catatan", 8: "Tidak tahu" };
const LABEL_HAMBATAN: Record<number, string> = {
  1: "Ya, sama sekali tidak bisa", 2: "Ya, banyak kesulitan dan membutuhkan bantuan",
  3: "Ya, sedikit kesulitan, tapi tidak membutuhkan bantuan", 4: "Tidak mengalami kesulitan",
};
const LABEL_KESEDIHAN: Record<number, string> = { 1: "Sangat sering", 2: "Sering", 3: "Jarang", 4: "Tidak pernah" };
const LABEL_PENYAKIT: Record<number, string> = {
  1: "Tidak ada", 2: "Hipertensi", 3: "Rematik", 4: "Asma", 5: "Masalah jantung",
  6: "Diabetes", 7: "Tuberculosis (TBC)", 8: "Stroke", 9: "Kanker atau tumor ganas",
  10: "Gagal ginjal", 11: "Haemophilia", 12: "HIV/AIDS", 13: "Kolesterol",
  14: "Sirosis hati", 15: "Thalasemia", 16: "Leukimia", 17: "Alzheimer", 18: "Lainnya",
};
const LABEL_STATUS_BANGUNAN: Record<number, string> = { 1: "Milik sendiri", 2: "Kontrak/sewa", 3: "Bebas sewa", 4: "Dinas", 5: "Lainnya" };
const LABEL_LANTAI: Record<number, string> = { 1: "Marmer/granit", 2: "Keramik", 3: "Parket/vinil/karpet", 4: "Ubin/tegel/teraso", 5: "Kayu/papan", 6: "Semen/bata merah", 7: "Bambu", 8: "Tanah", 9: "Lainnya" };
const LABEL_DINDING: Record<number, string> = { 1: "Tembok", 2: "Plesteran anyaman bambu/kawat", 3: "Kayu/papan/gypsum/GRC/calciboard", 4: "Anyaman bambu", 5: "Batang kayu", 6: "Bambu", 7: "Lainnya" };
const LABEL_ATAP: Record<number, string> = { 1: "Beton", 2: "Genteng", 3: "Seng", 4: "Asbes", 5: "Bambu", 6: "Kayu/sirap", 7: "Jerami/ijuk/daun-daunan/rumbia", 8: "Lainnya" };
const LABEL_AIR: Record<number, string> = {
  1: "Air kemasan bermerk", 2: "Air isi ulang", 3: "Leding", 4: "Sumur bor/pompa",
  5: "Sumur terlindung", 6: "Sumur tak terlindung", 7: "Mata air terlindung",
  8: "Mata air tak terlindung", 9: "Air permukaan (sungai/danau/waduk/kolam/irigasi)",
  10: "Air hujan", 11: "Lainnya",
};
const LABEL_FASILITAS_BAB: Record<number, string> = {
  1: "Ada, digunakan hanya anggota keluarga sendiri",
  2: "Ada, digunakan bersama keluarga tertentu",
  3: "Ada, di MCK komunal", 4: "Ada, di MCK umum",
  5: "Ada, anggota keluarga tidak menggunakan", 6: "Tidak ada fasilitas",
};
const LABEL_KLOSET: Record<number, string> = { 1: "Leher angsa", 2: "Plengsengan dengan tutup", 3: "Plengsengan tanpa tutup", 4: "Cemplung/cubluk" };
const LABEL_TINJA: Record<number, string> = { 1: "Tangki septik", 2: "IPAL", 3: "Kolam/sawah/sungai/danau/laut", 4: "Lubang tanah", 5: "Pantai/tanah lapang/kebun", 6: "Lainnya" };
const LABEL_PENERANGAN: Record<number, string> = { 1: "Listrik PLN dengan meteran", 2: "Listrik PLN tanpa meteran", 3: "Listrik non-PLN", 4: "Bukan listrik" };
const LABEL_BB_UTAMA: Record<number, string> = {
  0: "Tidak memasak di rumah", 1: "Listrik", 2: "Gas elpiji 5,5 kg/blue gaz",
  3: "Gas elpiji 12 kg", 4: "Gas elpiji 3 kg", 5: "Gas kota/meteran PGN",
  6: "Biogas", 7: "Minyak tanah", 8: "Briket", 9: "Arang", 10: "Kayu bakar", 11: "Lainnya",
};

const lbl = (map: Record<number, string>, val?: number) => (val !== undefined && val !== null ? map[val] ?? `ID ${val}` : "—");
const yaTidak = (val?: number) => (val === 1 ? "Ya" : val === 0 ? "Tidak" : "—");

// ─────────────────────────────────────────────────────────────────────────────

const DetailKeluarga: React.FC<DetailKeluargaProps> = ({ onLogout }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<KeluargaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const latestRequestRef = React.useRef(0);

  useEffect(() => {
    const requestId = ++latestRequestRef.current;
    const fetchData = async () => {
      try {
        if (id) {
          const result = await getKeluargaDetail(id);
          if (requestId === latestRequestRef.current) setData(result);
        }
      } catch (err) {
        if (requestId === latestRequestRef.current) console.error(err);
      } finally {
        if (requestId === latestRequestRef.current) setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <AdminLayout title="Detail Keluarga" onLogout={onLogout}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
          <Loader2 size={32} className="spin-icon" style={{ color: "#3b82f6", animation: "spin 1s linear infinite" }} />
        </div>
      </AdminLayout>
    );
  }

  if (!data) {
    return (
      <AdminLayout title="Detail Keluarga" onLogout={onLogout}>
        <div style={{ padding: "24px" }}>Data keluarga tidak ditemukan.</div>
      </AdminLayout>
    );
  }

  const desilAnggotaColor =
    data.desil_nasional_anggota === undefined ? "#64748b"
    : data.desil_nasional_anggota <= 3 ? "#ef4444"
    : data.desil_nasional_anggota <= 6 ? "#f97316"
    : "#22c55e";

  const desilKeluargaColor =
    data.desil_nasional_keluarga === undefined ? "#64748b"
    : data.desil_nasional_keluarga <= 3 ? "#ef4444"
    : data.desil_nasional_keluarga <= 6 ? "#f97316"
    : "#22c55e";

  const InfoRow = ({ label, value }: { label: string; value: string | number | undefined | null }) => (
    <div className="dk-info-row">
      <span className="dk-info-label">{label}</span>
      <span className="dk-info-value">{value ?? "—"}</span>
    </div>
  );

  const SectionCard = ({ icon, title, color, children }: { icon: React.ReactNode; title: string; color: string; children: React.ReactNode }) => (
    <div className="dk-card">
      <div className="dk-card-header">
        <div className={`dk-card-icon icon-${color}`}>{icon}</div>
        <h4 className="dk-card-title">{title}</h4>
      </div>
      <div className="dk-card-body">{children}</div>
    </div>
  );

  const AsetItem = ({ label, jumlah }: { label: string; jumlah: number }) => (
    <div className={`dk-aset-item ${jumlah > 0 ? "has-aset" : "no-aset"}`}>
      <span className="dk-aset-label">{label}</span>
      <span className="dk-aset-count">{jumlah > 0 ? jumlah : "—"}</span>
    </div>
  );

  return (
    <AdminLayout title="Detail Keluarga" onLogout={onLogout}>
      <div className="detail-keluarga-wrapper">
        {/* Back Button */}
        <button
          onClick={() => navigate(`/detail-hasil/${id}`)}
          style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            background: "none", border: "none", color: "#64748b",
            fontSize: "14px", fontWeight: 600, cursor: "pointer",
            marginBottom: "20px", padding: "8px 12px", borderRadius: "8px",
            transition: "all 0.2s", backgroundColor: "#f1f5f9",
          }}
          onMouseOver={(e) => { e.currentTarget.style.backgroundColor = "#e2e8f0"; e.currentTarget.style.color = "#334155"; }}
          onMouseOut={(e) => { e.currentTarget.style.backgroundColor = "#f1f5f9"; e.currentTarget.style.color = "#64748b"; }}
        >
          <ArrowLeft size={16} />
          Kembali ke Detail Hasil
        </button>

        {/* Page Header */}
        <div className="dk-header">
          <div>
            <h2 className="dk-title">Detail Keluarga</h2>
            <p className="dk-subtitle">Data lengkap keluarga untuk keperluan analisis bantuan sosial</p>
          </div>
          <div className="dk-id-badge">
            <span className="dk-id-label">No. KK</span>
            <span className="dk-id-value">{data.no_kk}</span>
          </div>
        </div>

        {/* Hero Info Strip */}
        <div className="dk-hero-strip">
          <div className="dk-hero-item">
            <span className="dk-hero-label">Nama Kepala Keluarga</span>
            <span className="dk-hero-value">{data.nama || "Tidak Diketahui"}</span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">NIK</span>
            <span className="dk-hero-value">{data.nik || "—"}</span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">Tempat / Tgl Lahir</span>
            <span className="dk-hero-value">{data.tempat_lahir || "—"} / {data.tanggal_lahir || "—"}</span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">Desil Anggota</span>
            <span className="dk-hero-desil" style={{ color: desilAnggotaColor, borderColor: desilAnggotaColor }}>
              Desil {data.desil_nasional_anggota ?? "-"}
            </span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">Desil Keluarga</span>
            <span className="dk-hero-desil" style={{ color: desilKeluargaColor, borderColor: desilKeluargaColor }}>
              Desil {data.desil_nasional_keluarga ?? "-"}
            </span>
          </div>
        </div>

        {/* Grid of Cards */}
        <div className="dk-grid">
          {/* Wilayah */}
          <SectionCard icon={<MapPin size={18} />} title="Informasi Wilayah" color="blue">
            <InfoRow label="Kabupaten/Kota" value={data.kabupaten_kota || data.kode_kabupaten_kota} />
            <InfoRow label="Kecamatan" value={data.kecamatan || data.kode_kecamatan} />
            <InfoRow label="Kelurahan/Desa" value={data.kelurahan_desa || data.kode_kelurahan_desa} />
            <InfoRow label="Alamat Domisili" value={data.alamat} />
            <InfoRow label="Jumlah Anggota" value={data.jumlah_anggota_keluarga !== undefined ? `${data.jumlah_anggota_keluarga} orang` : undefined} />
          </SectionCard>

          {/* Identitas & Bantuan */}
          <SectionCard icon={<FileText size={18} />} title="Identitas & Status" color="purple">
            <InfoRow label="Jenis Kelamin" value={lbl(LABEL_JENIS_KELAMIN, data.id_jenis_kelamin)} />
            <InfoRow label="Status Perkawinan" value={lbl(LABEL_STATUS_PERKAWINAN, data.id_status_perkawinan)} />
            <InfoRow label="Usia (2026)" value={data.umur_2026 !== undefined ? `${data.umur_2026} tahun` : undefined} />
            <InfoRow label="PBI" value={yaTidak(data.pbi)} />
            <InfoRow label="Status DTSEN" value={data.status_dtsen} />
            <InfoRow label="KPM Jawara" value={yaTidak(data.kpm_jawara)} />
            <InfoRow label="Putri Jawara" value={yaTidak(data.putri_jawara)} />
            <InfoRow label="PPKS Jawara" value={yaTidak(data.ppks_jawara)} />
            <InfoRow label="Kemiskinan Ekstrem" value={yaTidak(data.kemiskinan_ekstrem)} />
          </SectionCard>

          {/* Pendidikan & Pekerjaan */}
          <SectionCard icon={<Briefcase size={18} />} title="Pendidikan & Pekerjaan" color="orange">
            <InfoRow label="Partisipasi Sekolah" value={lbl(LABEL_PARTISIPASI_SEKOLAH, data.id_partisipasi_sekolah)} />
            <InfoRow label="Jenjang Pendidikan" value={lbl(LABEL_JENJANG, data.id_jenjang_pendidikan_dukcapil)} />
            <InfoRow label="Lapangan Usaha" value={lbl(LABEL_LAPANGAN_USAHA, data.id_lapangan_usaha_dari_usaha_utama)} />
            <InfoRow label="Status Kedudukan" value={lbl(LABEL_STATUS_KEDUDUKAN, data.id_status_kedudukan_pekerjaan_utama)} />
            <InfoRow label="Pekerjaan Utama" value={lbl(LABEL_LAPANGAN_USAHA, data.id_pekerjaan_utama)} />
            <InfoRow label="Omset Usaha" value={lbl(LABEL_OMSET, data.id_omset_usaha_utama)} />
            <InfoRow label="Jml Pekerja Dibayar" value={data.jumlah_pekerja_dibayar} />
            <InfoRow label="Jml Pekerja Tidak Dibayar" value={data.jumlah_pekerja_tidak_dibayar} />
          </SectionCard>

          {/* Kesehatan & Disabilitas */}
          <SectionCard icon={<Heart size={18} />} title="Kesehatan & Disabilitas" color="purple">
            <InfoRow label="Kondisi Gizi" value={lbl(LABEL_KONDISI_GIZI, data.id_kondisi_gizi)} />
            <InfoRow label="Penyakit Menahun" value={lbl(LABEL_PENYAKIT, data.id_penyakit_menahun)} />
            <InfoRow label="Kesedihan/Depresi" value={lbl(LABEL_KESEDIHAN, data.id_kesedihan_depresi)} />
            <InfoRow label="Penglihatan" value={lbl(LABEL_HAMBATAN, data.id_penglihatan)} />
            <InfoRow label="Pendengaran" value={lbl(LABEL_HAMBATAN, data.id_pendengaran)} />
            <InfoRow label="Berjalan/Naik Tangga" value={lbl(LABEL_HAMBATAN, data.id_berjalan_atau_naik_tangga)} />
            <InfoRow label="Menggunakan Tangan/Jari" value={lbl(LABEL_HAMBATAN, data.id_menggunakan_tangan_jari)} />
            <InfoRow label="Kemampuan Intelektual" value={lbl(LABEL_HAMBATAN, data.id_belajar_kemampuan_intelektual)} />
            <InfoRow label="Pengendalian Perilaku" value={lbl(LABEL_HAMBATAN, data.id_pengendalian_perilaku)} />
            <InfoRow label="Berbicara/Komunikasi" value={lbl(LABEL_HAMBATAN, data.id_berbicara_komunikasi)} />
            <InfoRow label="Mengurus Diri" value={lbl(LABEL_HAMBATAN, data.id_mengurus_diri)} />
            <InfoRow label="Mengingat/Berkonsentrasi" value={lbl(LABEL_HAMBATAN, data.id_mengingat_berkonsentrasi)} />
          </SectionCard>

          {/* Kondisi Rumah */}
          <SectionCard icon={<Home size={18} />} title="Kondisi Perumahan" color="green">
            <InfoRow label="Status Kepemilikan" value={lbl(LABEL_STATUS_BANGUNAN, data.id_status_penguasaan_bangunan)} />
            <InfoRow label="Luas Lantai" value={data.luas_lantai_bangunan !== undefined ? `${data.luas_lantai_bangunan} m²` : undefined} />
            <InfoRow label="Jenis Lantai Terluas" value={lbl(LABEL_LANTAI, data.id_lantai_terluas)} />
            <InfoRow label="Jenis Dinding Terluas" value={lbl(LABEL_DINDING, data.id_dinding_terluas)} />
            <InfoRow label="Jenis Atap Terluas" value={lbl(LABEL_ATAP, data.id_atap_terluas)} />
          </SectionCard>

          {/* Utilitas */}
          <SectionCard icon={<Monitor size={18} />} title="Utilitas & Sanitasi" color="orange">
            <InfoRow label="Sumber Air Minum" value={lbl(LABEL_AIR, data.id_sumber_airminum)} />
            <InfoRow label="Sumber Penerangan" value={lbl(LABEL_PENERANGAN, data.id_sumberpenerangan)} />
            <InfoRow label="Bahan Bakar Masak" value={lbl(LABEL_BB_UTAMA, data.id_bb_utama)} />
            <InfoRow label="Fasilitas BAB" value={lbl(LABEL_FASILITAS_BAB, data.id_fasilitas_bab)} />
            <InfoRow label="Jenis Kloset" value={lbl(LABEL_KLOSET, data.id_jenis_kloset)} />
            <InfoRow label="Pembuangan Tinja" value={lbl(LABEL_TINJA, data.id_pembuangan_tinja)} />
          </SectionCard>

          {/* Kepemilikan Aset */}
          <SectionCard icon={<ShieldCheck size={18} />} title="Kepemilikan Aset Bergerak" color="blue">
            <div className="dk-aset-grid">
              <AsetItem label="Tabung Gas" jumlah={data.aset_bergerak_tabung_gas ?? 0} />
              <AsetItem label="Kulkas" jumlah={data.aset_bergerak_lemari_es ?? 0} />
              <AsetItem label="AC" jumlah={data.aset_bergerak_ac ?? 0} />
              <AsetItem label="Water Heater" jumlah={data.aset_bergerak_pemanas_air ?? 0} />
              <AsetItem label="TV" jumlah={data.aset_bergerak_tv_datar ?? 0} />
              <AsetItem label="Emas/Perhiasan" jumlah={data.aset_bergerak_emas_perhiasan ?? 0} />
              <AsetItem label="Komputer/Laptop" jumlah={data.aset_bergerak_komputer_laptop_tablet ?? 0} />
              <AsetItem label="Sepeda Motor" jumlah={data.aset_bergerak_sepeda_motor ?? 0} />
              <AsetItem label="Sepeda" jumlah={data.aset_bergerak_sepeda ?? 0} />
              <AsetItem label="Mobil" jumlah={data.aset_bergerak_mobil ?? 0} />
              <AsetItem label="Perahu" jumlah={data.aset_bergerak_perahu ?? 0} />
              <AsetItem label="Kapal Motor" jumlah={data.aset_bergerak_kapal_perahu_motor ?? 0} />
              <AsetItem label="Smartphone" jumlah={data.aset_bergerak_smartphone ?? 0} />
              <AsetItem label="Telepon Rumah" jumlah={data.aset_bergerak_telepon_rumah ?? 0} />
              <AsetItem label="Lahan di Tempat Lain" jumlah={data.lahan_tempat_lain ?? 0} />
              <AsetItem label="Rumah di Tempat Lain" jumlah={data.rumah_tempat_lain ?? 0} />
            </div>
          </SectionCard>

          {/* Ternak */}
          <SectionCard icon={<Leaf size={18} />} title="Kepemilikan Ternak" color="green">
            <div className="dk-aset-grid">
              <AsetItem label="Sapi" jumlah={data.jml_sapi ?? 0} />
              <AsetItem label="Kerbau" jumlah={data.jml_kerbau ?? 0} />
              <AsetItem label="Kuda" jumlah={data.jml_kuda ?? 0} />
              <AsetItem label="Babi" jumlah={data.jml_babi ?? 0} />
              <AsetItem label="Kambing/Domba" jumlah={data.jml_kambing_domba ?? 0} />
            </div>
          </SectionCard>
        </div>
      </div>
    </AdminLayout>
  );
};

export default DetailKeluarga;
