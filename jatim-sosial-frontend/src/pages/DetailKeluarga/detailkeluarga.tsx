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
} from "lucide-react";
import { getKeluargaDetail, type KeluargaDetail } from "../../services/api";
import "./DetailKeluarga.css";

interface DetailKeluargaProps {
  onLogout?: () => void;
}

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
          if (requestId === latestRequestRef.current) {
            setData(result);
          }
        }
      } catch (err) {
        if (requestId === latestRequestRef.current) {
          console.error(err);
        }
      } finally {
        if (requestId === latestRequestRef.current) {
          setLoading(false);
        }
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <AdminLayout title="Detail Keluarga" onLogout={onLogout}>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
          }}
        >
          <Loader2
            size={32}
            className="spin-icon"
            style={{ color: "#3b82f6", animation: "spin 1s linear infinite" }}
          />
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

  const desilColor =
    data.desil_nasional === undefined
      ? "#64748b"
      : data.desil_nasional <= 3
        ? "#ef4444"
        : data.desil_nasional <= 6
          ? "#f97316"
          : "#22c55e";

  const InfoRow = ({
    label,
    value,
  }: {
    label: string;
    value: string | number | undefined | null;
  }) => (
    <div className="dk-info-row">
      <span className="dk-info-label">{label}</span>
      <span className="dk-info-value">{value ?? "—"}</span>
    </div>
  );

  const SectionCard = ({
    icon,
    title,
    color,
    children,
  }: {
    icon: React.ReactNode;
    title: string;
    color: string;
    children: React.ReactNode;
  }) => (
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
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            background: "none",
            border: "none",
            color: "#64748b",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            marginBottom: "20px",
            padding: "8px 12px",
            borderRadius: "8px",
            transition: "all 0.2s",
            backgroundColor: "#f1f5f9",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = "#e2e8f0";
            e.currentTarget.style.color = "#334155";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = "#f1f5f9";
            e.currentTarget.style.color = "#64748b";
          }}
        >
          <ArrowLeft size={16} />
          Kembali ke Detail Hasil
        </button>

        {/* Page Header */}
        <div className="dk-header">
          <div>
            <h2 className="dk-title">Detail Keluarga</h2>
            <p className="dk-subtitle">
              Data lengkap keluarga untuk keperluan analisis bantuan sosial
            </p>
          </div>
          <div className="dk-id-badge">
            <span className="dk-id-label">ID Keluarga</span>
            <span className="dk-id-value">{data.id_keluarga}</span>
          </div>
        </div>

        {/* Hero Info Strip */}
        <div className="dk-hero-strip">
          <div className="dk-hero-item">
            <span className="dk-hero-label">Nama Kepala Keluarga</span>
            <span className="dk-hero-value">
              {data.nama_anggota_keluarga || "Tidak Diketahui"}
            </span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">NIK / No. Identitas</span>
            <span className="dk-hero-value">{data.nik || "—"}</span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">No. KK</span>
            <span className="dk-hero-value">{data.nomor_kartu_keluarga}</span>
          </div>
          <div className="dk-hero-divider" />
          <div className="dk-hero-item">
            <span className="dk-hero-label">Desil Kesejahteraan</span>
            <span
              className="dk-hero-desil"
              style={{ color: desilColor, borderColor: desilColor }}
            >
              Desil {data.desil_nasional || "-"}
            </span>
          </div>
        </div>

        {/* Grid of Cards */}
        <div className="dk-grid">
          {/* Wilayah */}
          <SectionCard
            icon={<MapPin size={18} />}
            title="Informasi Wilayah"
            color="blue"
          >
            <InfoRow
              label="Provinsi"
              value={data.provinsi || data.kode_provinsi}
            />
            <InfoRow
              label="Kabupaten/Kota"
              value={data.kabupaten_kota || data.kode_kabupaten_kota}
            />
            <InfoRow
              label="Kecamatan"
              value={data.kecamatan || data.kode_kecamatan}
            />
            <InfoRow
              label="Kelurahan/Desa"
              value={data.kelurahan_desa || data.kode_kelurahan_desa}
            />
            <InfoRow label="Alamat Domisili" value={data.alamat} />
          </SectionCard>

          {/* Identitas */}
          <SectionCard
            icon={<FileText size={18} />}
            title="Identitas & Bantuan"
            color="purple"
          >
            <InfoRow
              label="Jumlah Anggota"
              value={`${data.jumlah_anggota_keluarga || 0} orang`}
            />
            <InfoRow
              label="ID Pelanggan PLN"
              value={data.id_pelanggan_pln || "—"}
            />
            <InfoRow
              label="Bantuan Iuran Nasional"
              value={data.pbi_nas ? "YA" : "TIDAK"}
            />
            <InfoRow
              label="Bantuan Iuran Pemda"
              value={data.pbi_pemda ? "YA" : "TIDAK"}
            />
          </SectionCard>

          {/* Kondisi Rumah */}
          <SectionCard
            icon={<Home size={18} />}
            title="Kondisi Perumahan"
            color="green"
          >
            <InfoRow
              label="Status Kepemilikan"
              value={data.status_kepemilikan_rumah}
            />
            <InfoRow
              label="Luas Lantai"
              value={`${data.luas_lantai || 0} m²`}
            />
            <InfoRow
              label="Jenis Lantai Terluas"
              value={data.jenis_lantai_terluas}
            />
            <InfoRow
              label="Jenis Dinding Terluas"
              value={data.jenis_dinding_terluas}
            />
            <InfoRow
              label="Jenis Atap Terluas"
              value={data.jenis_atap_terluas}
            />
          </SectionCard>

          {/* Utilitas */}
          <SectionCard
            icon={<Monitor size={18} />}
            title="Utilitas & Sanitasi"
            color="orange"
          >
            <InfoRow
              label="Sumber Air Minum"
              value={data.sumber_air_minum_utama}
            />
            <InfoRow
              label="Sumber Penerangan"
              value={data.sumber_penerangan_utama}
            />
            <InfoRow
              label="Daya Listrik Terpasang"
              value={data.daya_terpasang}
            />
            <InfoRow
              label="Bahan Bakar Masak"
              value={data.bahan_bakar_utama_memasak}
            />
            <InfoRow label="Fasilitas BAB" value={data.fasilitas_bab} />
            <InfoRow label="Jenis Kloset" value={data.jenis_kloset} />
            <InfoRow
              label="Pembuangan Tinja"
              value={data.pembuangan_akhir_tinja}
            />
          </SectionCard>

          {/* Kepemilikan Aset */}
          <SectionCard
            icon={<ShieldCheck size={18} />}
            title="Kepemilikan Aset Bergerak"
            color="blue"
          >
            <div className="dk-aset-grid">
              <AsetItem
                label="Tabung Gas"
                jumlah={data.aset_bergerak_tabung_gas ? 1 : 0}
              />
              <AsetItem
                label="Kulkas"
                jumlah={data.aset_bergerak_lemari_es ? 1 : 0}
              />
              <AsetItem label="AC" jumlah={data.aset_bergerak_ac ? 1 : 0} />
              <AsetItem
                label="Water Heater"
                jumlah={data.aset_bergerak_pemanas_air ? 1 : 0}
              />
              <AsetItem
                label="TV"
                jumlah={data.aset_bergerak_tv_datar ? 1 : 0}
              />
              <AsetItem
                label="Emas"
                jumlah={data.aset_bergerak_emas_perhiasan ? 1 : 0}
              />
              <AsetItem
                label="Komputer/Laptop"
                jumlah={data.aset_bergerak_komputer_laptop_tablet ? 1 : 0}
              />
              <AsetItem
                label="Sepeda Motor"
                jumlah={data.aset_bergerak_sepeda_motor ? 1 : 0}
              />
              <AsetItem
                label="Sepeda"
                jumlah={data.aset_bergerak_sepeda ? 1 : 0}
              />
              <AsetItem
                label="Mobil"
                jumlah={data.aset_bergerak_mobil ? 1 : 0}
              />
              <AsetItem
                label="Perahu"
                jumlah={data.aset_bergerak_perahu ? 1 : 0}
              />
              <AsetItem
                label="Kapal Motor"
                jumlah={data.aset_bergerak_kapal_perahu_motor ? 1 : 0}
              />
              <AsetItem
                label="Smartphone"
                jumlah={data.aset_bergerak_smartphone ? 1 : 0}
              />
              <AsetItem
                label="Telepon Rumah"
                jumlah={data.aset_bergerak_telepon_rumah ? 1 : 0}
              />
              <AsetItem
                label="Lahan Lain"
                jumlah={data.aset_tidak_bergerak_lahan_lainnya ? 1 : 0}
              />
              <AsetItem
                label="Rumah Lain"
                jumlah={data.aset_tidak_bergerak_rumah_lainnya ? 1 : 0}
              />
            </div>
          </SectionCard>

          {/* Ternak */}
          <SectionCard
            icon={<Leaf size={18} />}
            title="Kepemilikan Ternak"
            color="green"
          >
            <div className="dk-aset-grid">
              <AsetItem label="Sapi" jumlah={data.jumlah_ternak_sapi || 0} />
              <AsetItem
                label="Kerbau"
                jumlah={data.jumlah_ternak_kerbau || 0}
              />
              <AsetItem label="Kuda" jumlah={data.jumlah_ternak_kuda || 0} />
              <AsetItem label="Babi" jumlah={data.jumlah_ternak_babi || 0} />
              <AsetItem
                label="Kambing/Domba"
                jumlah={data.jumlah_ternak_kambing_domba || 0}
              />
            </div>
          </SectionCard>
        </div>
      </div>
    </AdminLayout>
  );
};

export default DetailKeluarga;
