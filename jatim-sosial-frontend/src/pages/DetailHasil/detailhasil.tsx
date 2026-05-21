import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { apiFetch } from "../../services/api";
import { type Tahap } from "../../data/mockData";
import AdminLayout from "../../components/layout/AdminLayout";
import { RecommendationCard } from "../../components/cards/RecommendationCard";
import {
  FileText,
  User,
  Home,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  ThumbsUp,
  RefreshCw
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import "./DetailHasil.css";

interface DetailHasilProps {
  onLogout?: () => void;
}

interface DetailKeluargaResponse {
  id_keluarga: string;
  idLabel: string;
  tanggal: string;
  nama: string;
  nik: string;
  wilayah: string;
  kecamatan: string;
  desil: number;
  skorKesejahteraan: number;
  tahap: Tahap;
  bantuan: string[];
  rekomendasiBantuan: string[];
  skorASPD: number;
  skorPKHT: number;
  atap: number;
  dinding: number;
  lantai: number;
  url_foto?: string | null;
  foto_urls?: string[];
  visual_match?: boolean | null;
  visual_reasoning?: string | null;
  aiReasoning: string;
  catatan?: string | null;
  catatan_supervisor?: string | null;
}

const mapAtap = (val: number) => {
  const map: Record<number, string> = { 1: "Beton", 2: "Genteng Tanah Liat", 3: "Asbes", 4: "Seng", 5: "Bambu", 6: "Jerami/Ijuk", 7: "Lainnya" };
  return map[val] || "Tidak Diketahui";
};

const mapDinding = (val: number) => {
  const map: Record<number, string> = { 1: "Tembok", 2: "Kayu", 3: "Bambu", 4: "Tanah", 5: "Lainnya" };
  return map[val] || "Tidak Diketahui";
};

const mapLantai = (val: number) => {
  const map: Record<number, string> = { 1: "Marmer/Granit", 2: "Keramik", 3: "Ubin/Semen", 4: "Kayu", 5: "Bambu", 6: "Tanah", 7: "Lainnya" };
  return map[val] || "Tidak Diketahui";
};

const DetailHasil: React.FC<DetailHasilProps> = ({ onLogout }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [detailData, setDetailData] = useState<DetailKeluargaResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const familyId = id || location.state?.id_keluarga;

  const [stageState, setStageState] = useState<Tahap>(location.state?.tahap || "analisis");
  const [selectedPrograms, setSelectedPrograms] = useState<string[]>(location.state?.bantuan || []);
  const [isConfirming, setIsConfirming] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [isAssistanceConfirmed, setIsAssistanceConfirmed] = useState(false);
  const [catatanInput, setCatatanInput] = useState("");
  const [catatanSupInput, setCatatanSupInput] = useState("");

  const displayImages = (() => {
    const urls = [...(detailData?.foto_urls || [])];
    
    // Replace minio hostnames if needed
    const processedUrls = urls.map(url => 
      url.replace('http://minio:9000', `http://${window.location.hostname}:9000`)
    );

    // If there is only one photo or it's empty, and we have a url_foto
    if (processedUrls.length === 0 && detailData?.url_foto) {
      processedUrls.push(detailData.url_foto.replace('http://minio:9000', `http://${window.location.hostname}:9000`));
    }

    return processedUrls;
  })();

  const renderVisualMatchBadge = (match: boolean | null | undefined) => {
    if (match === undefined || match === null) {
      return (
        <span
          style={{
            display: "inline-block",
            width: "110px",
            textAlign: "center",
            padding: "6px 0",
            borderRadius: "9999px",
            fontSize: "11px",
            fontWeight: 700,
            backgroundColor: "#f1f5f9",
            color: "#64748b",
          }}
        >
          Belum Diases
        </span>
      );
    }

    if (match === true) {
      return (
        <span
          style={{
            display: "inline-block",
            width: "110px",
            textAlign: "center",
            padding: "6px 0",
            borderRadius: "9999px",
            fontSize: "11px",
            fontWeight: 700,
            backgroundColor: "#ecfdf5",
            color: "#10b981",
          }}
        >
          Sesuai
        </span>
      );
    }

    return (
      <span
        style={{
          display: "inline-block",
          width: "110px",
          textAlign: "center",
          padding: "6px 0",
          borderRadius: "9999px",
          fontSize: "11px",
          fontWeight: 700,
          backgroundColor: "#fef2f2",
          color: "#ef4444",
        }}
      >
        Tidak Sesuai
      </span>
    );
  };

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await apiFetch(`/api/v1/manajemen-bantuan/${familyId}`);
        if (res.ok) {
          const data = await res.json();
          setDetailData(data);
          
          setStageState(data.tahap);
          setSelectedPrograms(data.tahap !== "analisis" ? data.bantuan : []);
          setIsAssistanceConfirmed(data.tahap !== "analisis");
          if (data.catatan) setCatatanInput(data.catatan);
          if (data.catatan_supervisor) setCatatanSupInput(data.catatan_supervisor);
        }
      } catch (err) {
        console.error("Gagal mengambil data detail", err);
      } finally {
        setIsLoading(false);
      }
    };
    if (familyId) fetchDetail();
  }, [familyId]);

  const currentTahap = stageState;
  const isFinalized = currentTahap !== "analisis";

  const desil = detailData?.desil || location.state?.desil || 1;
  const namaKeluarga = detailData?.nama || location.state?.nama || "-";
  const nik = detailData?.nik || location.state?.nik || "-";
  const wilayah = detailData?.wilayah || location.state?.wilayah || "-";
  const kecamatan = detailData?.kecamatan || location.state?.kecamatan || "-";
  const tanggal = detailData?.tanggal || location.state?.tanggal || "-";

  const familyScores = {
    aspd: detailData?.skorASPD || 0,
    pkht: detailData?.skorPKHT || 0,
  };

  const recommendations: any[] = [
    {
      id: "ASPD",
      title: "ASPD (Asistensi Sosial Penyandang Disabilitas)",
      match: familyScores.aspd,
      desc: "Bantuan sosial tunai dari Pemerintah Provinsi Jawa Timur untuk penyandang disabilitas berat guna memenuhi kebutuhan dasar dan meningkatkan kualitas hidup mereka.",
      reason:
        "Keluarga memenuhi kriteria prioritas dengan skor kelayakan tinggi.",
      isReceived: false,
    },
    {
      id: "PKHT",
      title: "PKH Plus (Program Keluarga Harapan Plus)",
      match: familyScores.pkht,
      desc: "Bantuan sosial bersyarat berupa dana tunai khusus bagi lanjut usia (lansia) berusia 70 tahun ke atas dari keluarga sangat miskin yang terdaftar dalam DTKS.",
      reason:
        "Analisis kriteria kesehatan dan pendidikan menunjukkan kelayakan tinggi.",
      isReceived: false,
    },
    {
      id: "KE",
      title: "Bantuan Kemiskinan Ekstrem",
      match: 40,
      desc: "Program percepatan penghapusan kemiskinan ekstrem melalui bantuan modal usaha ekonomi produktif, rehabilitasi hunian, dan jaminan sosial bagi keluarga miskin ekstrem.",
      reason: "Potensi pengembangan usaha mikro mandiri.",
      isReceived: false,
    },
    {
      id: "JAWARA",
      title: "KIP KPM Jawara",
      match: 0,
      desc: "Program beasiswa Kartu Indonesia Pintar (KIP) yang disasarkan khusus untuk anak-anak sekolah dari Keluarga Penerima Manfaat (KPM) program Jatim Jawara.",
      reason: "Tidak ada data indikator yang terpenuhi",
      isReceived: false,
    },
    {
      id: "JAWARA P",
      title: "KIP Putri Jawara",
      match: 0,
      desc: "Bantuan pendidikan khusus berupa beasiswa Kartu Indonesia Pintar (KIP) bagi anak perempuan dari keluarga rentan dan miskin untuk mencegah angka putus sekolah.",
      reason: "Tidak ada data indikator yang terpenuhi",
      isReceived: false,
    },
    {
      id: "PPU",
      title: "KIP PPKS Jawara",
      match: 0,
      desc: "Program dukungan pendidikan beasiswa Kartu Indonesia Pintar (KIP) untuk anak-anak Pemerlu Pelayanan Kesejahteraan Sosial (PPKS) seperti anak asuh, yatim piatu, dll.",
      reason: "Tidak ada data indikator yang terpenuhi",
      isReceived: false,
    },
  ];

  const familyRecs = detailData?.rekomendasiBantuan || [];

  const filteredRecommendations = recommendations.filter((rec) => {
    return familyRecs.includes(rec.id);
  });

  const otherRecommendations = recommendations.filter((rec) => {
    return !familyRecs.includes(rec.id);
  });

  const handleToggleProgram = (id: string) => {
    if (isFinalized || isAssistanceConfirmed) return;

    setSelectedPrograms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  const handleUpdateStatus = async (status: string, bantuanList?: string[], catatan?: string, catatan_supervisor?: string) => {
    try {
      const response = await apiFetch(`/api/v1/manajemen-bantuan/${id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status_validasi: status,
          bantuan: bantuanList,
          catatan: catatan,
          catatan_supervisor: catatan_supervisor
        })
      });
      if (!response.ok) throw new Error("Gagal update status");
      
      const data = await response.json();
      setDetailData(data);
      setStageState(status as Tahap);
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  const handleConfirmAssistance = async () => {
    if (selectedPrograms.length === 0) return;
    setIsConfirming(true);
    const success = await handleUpdateStatus("validasi", selectedPrograms, catatanInput);
    setIsConfirming(false);
    if (success) {
      setSuccessMsg("Rekomendasi bantuan berhasil diajukan ke tahap Validasi!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleSupervisorApprove = async () => {
    const success = await handleUpdateStatus("diterima", selectedPrograms, undefined, catatanSupInput);
    if (success) {
      setSuccessMsg("Bantuan Sosial Berhasil Disetujui!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleSupervisorReject = async () => {
    const success = await handleUpdateStatus("ditolak", undefined, undefined, catatanSupInput);
    if (success) {
      setSuccessMsg("Pengajuan Bantuan Sosial Ditolak!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleReanalyze = async () => {
    const success = await handleUpdateStatus("analisis");
    if (success) {
      setSuccessMsg("Status dikembalikan ke tahap Analisis!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  if (isLoading) {
    return (
      <AdminLayout title="Detail Analisis" onLogout={onLogout}>
        <div className="flex items-center justify-center h-full">
          <p>Memuat data detail...</p>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Detail Analisis" onLogout={onLogout}>
      <div className="detail-page-wrapper">
        {/* Header Options */}
        <div className="detail-page-header flex-between">
          <div>
            <h2 className="title-family">
              Keluarga {namaKeluarga}
              <span className="badge-ai-verified">DESIL {desil}</span>
            </h2>
            <p className="subtitle-family">
              ID / NIK: {nik} • Kecamatan {kecamatan}, {wilayah} • Data per{" "}
              {tanggal}
            </p>
          </div>
          <div className="header-actions">
            <button
              className="btn-primary"
              onClick={() => navigate(`/detail-keluarga/${familyId}`)}
            >
              <User size={16} /> Lihat Data Keluarga
            </button>
          </div>
        </div>

        {/* Success Notification */}
        {successMsg && (
          <div className="notification-toast success">
            <CheckCircle size={20} />
            {successMsg}
          </div>
        )}

        {/* Content Layout */}
        <div className="detail-content-layout">
          {/* Left Column (Main Anal  ysis Data) */}
          <div className="detail-main-col">
            {/* Validator / Validasi Section */}
            <div className="detail-card-section">
              <div className="detail-card-header">
                <Home size={18} className="text-blue" />
                <h4>Validator / Validasi</h4>
              </div>
              <div className="detail-card-body">
                {/* Foto Grid atau Single (Side-by-Side untuk Tampak Luar & Tampak Dalam) */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    gap: "20px",
                    marginBottom: "24px",
                    flexWrap: "wrap",
                  }}
                >
                  {displayImages.length > 0 ? (
                    displayImages.map((imgUrl, index) => (
                      <div
                        key={index}
                        className="visual-image-wrapper"
                        style={{
                          width: displayImages.length > 1 ? "47%" : "60%",
                          minWidth: "260px",
                          maxWidth: displayImages.length > 1 ? "360px" : "500px",
                        }}
                      >
                        <div className="placeholder-image" style={{ overflow: 'hidden', position: 'relative', height: '240px' }}>
                          <img 
                            src={imgUrl} 
                            alt={`Survey Hunian ${index === 0 ? "Tampak Luar" : "Tampak Dalam"}`} 
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                          />
                          <div style={{ position: 'absolute', bottom: 10, left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.65)', color: 'white', padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}>
                            {index === 0 ? "Foto 1: Tampak Luar" : "Foto 2: Tampak Dalam"}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div
                      className="visual-image-wrapper"
                      style={{ width: "60%", maxWidth: "500px" }}
                    >
                      <div className="placeholder-image">
                        <Home size={48} className="text-gray-400" />
                        <span className="img-caption">
                          Foto Survey Hunian Lapangan
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Tabel 4x4 Bersih: Variabel, Data DTKS, Status, Alasan */}
                <div
                  className="table-responsive"
                  style={{
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    overflow: "hidden",
                    marginBottom: "0px",
                  }}
                >
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "13px",
                    }}
                  >
                    <thead>
                      <tr
                        style={{
                          backgroundColor: "#f8fafc",
                          borderBottom: "1px solid #e2e8f0",
                        }}
                      >
                        <th
                          style={{
                            padding: "12px 16px",
                            textAlign: "left",
                            fontWeight: 600,
                            color: "#475569",
                          }}
                        >
                          VARIABEL
                        </th>
                        <th
                          style={{
                            padding: "12px 16px",
                            textAlign: "left",
                            fontWeight: 600,
                            color: "#475569",
                          }}
                        >
                          DATA REGISTER
                        </th>
                        <th
                          style={{
                            padding: "12px 16px",
                            textAlign: "left",
                            fontWeight: 600,
                            color: "#475569",
                          }}
                        >
                          STATUS
                        </th>
                        <th
                          style={{
                            padding: "12px 16px",
                            textAlign: "left",
                            fontWeight: 600,
                            color: "#475569",
                          }}
                        >
                          ALASAN DETEKSI
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                        <td
                          style={{
                            padding: "14px 16px",
                            fontWeight: 600,
                            color: "#1e293b",
                          }}
                        >
                          Atap
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
                          {mapAtap(detailData?.atap || 0)}
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          {renderVisualMatchBadge(detailData?.visual_match)}
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
                          {detailData?.visual_reasoning || "-"}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                        <td
                          style={{
                            padding: "14px 16px",
                            fontWeight: 600,
                            color: "#1e293b",
                          }}
                        >
                          Dinding
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
                          {mapDinding(detailData?.dinding || 0)}
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          {renderVisualMatchBadge(detailData?.visual_match)}
                        </td>
                        <td
                          style={{ padding: "14px 16px", color: "#475569" }}
                        >
                          -
                        </td>
                      </tr>
                      <tr>
                        <td
                          style={{
                            padding: "14px 16px",
                            fontWeight: 600,
                            color: "#1e293b",
                          }}
                        >
                          Lantai
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
                          {mapLantai(detailData?.lantai || 0)}
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          {renderVisualMatchBadge(detailData?.visual_match)}
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
                          -
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            {/* AI Summary Section (mkn3 reasoning) */}
            <div className="detail-card-section">
              <div className="detail-card-header">
                <FileText size={18} className="text-blue" />
                <h4>Ringkasan Singkat & Rekomendasi</h4>
              </div>
              <div className="detail-card-body" style={{ lineHeight: '1.6', color: '#4a5568', fontSize: '14px' }}>
                <ReactMarkdown>
                  {location.state?.aiReasoning || 'Data reasoning belum tersedia dari AI.'}
                </ReactMarkdown>
              </div>
            </div>

            {/* Smart Recommendations Section */}
            {currentTahap !== "diterima" && (
              <div className="recommendations-container">
                <h3 className="section-title-large">
                  Rekomendasi Utama (Analisis AI)
                </h3>
                <div
                  className="recommendation-cards-grid"
                  style={{ marginBottom: "28px" }}
                >
                  {filteredRecommendations.length === 0 ? (
                    <div
                      style={{
                        gridColumn: "1 / -1",
                        padding: "32px 24px",
                        backgroundColor: "#f8fafc",
                        border: "1px dashed #cbd5e1",
                        borderRadius: "12px",
                        textAlign: "center",
                        color: "#64748b",
                      }}
                    >
                      <AlertCircle
                        size={32}
                        style={{ margin: "0 auto 8px", color: "#94a3b8" }}
                      />
                      <p
                        style={{
                          fontWeight: 600,
                          fontSize: "14px",
                          color: "#334155",
                        }}
                      >
                        Tidak Ada Rekomendasi Program Bantuan
                      </p>
                      <p
                        style={{
                          fontSize: "12px",
                          marginTop: "4px",
                          color: "#64748b",
                        }}
                      >
                        Keluarga ini tidak memenuhi indikasi kelayakan untuk
                        program ASPD, PKHT, atau KE.
                      </p>
                    </div>
                  ) : (
                    filteredRecommendations.map((rec) => (
                      <RecommendationCard
                        key={rec.id}
                        data={rec}
                        isSelected={selectedPrograms.includes(rec.id)}
                        isLocked={isFinalized || isAssistanceConfirmed}
                        onToggle={handleToggleProgram}
                      />
                    ))
                  )}
                </div>

                <h3
                  className="section-title-large"
                  style={{ marginTop: "28px" }}
                >
                  Program Bantuan Lainnya (Pilihan Alternatif)
                </h3>
                <div className="recommendation-cards-grid">
                  {otherRecommendations.length === 0 ? (
                    <p style={{ color: "#94a3b8", fontSize: "13px" }}>
                      Tidak ada pilihan program bantuan lainnya.
                    </p>
                  ) : (
                    otherRecommendations.map((rec) => (
                      <RecommendationCard
                        key={rec.id}
                        data={{
                          ...rec,
                          match: 0, // Menjamin kartu putih premium
                        }}
                        isSelected={selectedPrograms.includes(rec.id)}
                        isLocked={isFinalized || isAssistanceConfirmed}
                        onToggle={handleToggleProgram}
                      />
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Selected Assistance Confirmation Area */}
            {selectedPrograms.length > 0 && currentTahap !== "diterima" && (
              <div
                className={`selected-assistance-section ${isFinalized ? "finalized" : isAssistanceConfirmed ? "finalized" : ""}`}
                style={
                  isAssistanceConfirmed && !isFinalized
                    ? { borderColor: "#bbf7d0", backgroundColor: "#f0fdf4" }
                    : {}
                }
              >
                <div className="flex-between max-w-full">
                  <div>
                    <h4>
                      {isFinalized
                        ? "Bantuan yang Akan Diterima (Disetujui)"
                        : isAssistanceConfirmed
                          ? "Bantuan Terkonfirmasi (Belum Dikirim)"
                          : "Bantuan yang Akan Diterima"}
                    </h4>
                    <p>
                      Program yang dipilih:{" "}
                      {selectedPrograms
                        .map(
                          (id) =>
                            recommendations.find((r) => r.id === id)?.title ||
                            id,
                        )
                        .join(", ")}
                    </p>
                  </div>
                  {!isFinalized && (
                    <div style={{ display: "flex", gap: "8px" }}>
                      {isAssistanceConfirmed ? (
                        <>
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              color: "#16a34a",
                              fontWeight: 600,
                              fontSize: "13px",
                              background: "#dcfce7",
                              padding: "6px 12px",
                              borderRadius: "6px",
                              border: "1px solid #bbf7d0",
                            }}
                          >
                            <CheckCircle size={14} /> Terkonfirmasi
                          </span>
                          <button
                            className="btn-outline"
                            onClick={() => setIsAssistanceConfirmed(false)}
                            style={{ padding: "6px 12px", fontSize: "13px" }}
                          >
                            Ubah Bantuan
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn-confirm-assistance"
                          onClick={() => setIsAssistanceConfirmed(true)}
                          style={{ padding: "8px 16px", fontSize: "13px" }}
                        >
                          Konfirmasi Bantuan
                        </button>
                      )}
                    </div>
                  )}
                  {isFinalized && (
                    <span className="badge-final">
                      <CheckCircle size={16} /> Final Decision
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column (Dynamic Panel based on Tahap) */}
          <div className="detail-side-col">
            {/* PANEL: ANALISIS */}
            {currentTahap === "analisis" && (
              <div className="validation-panel">
                <div className="panel-header">
                  <ShieldCheck size={18} className="text-blue" />
                  <h4>Analisis</h4>
                </div>
                <div className="panel-body">
                  <div className="form-group">
                    <label>Catatan Analisis</label>
                    <textarea
                      placeholder="Tambahkan observasi lapangan atau catatan analisis..."
                      rows={5}
                      value={catatanInput}
                      onChange={(e) => setCatatanInput(e.target.value)}
                    ></textarea>
                  </div>
                  <div
                    className="panel-actions"
                    style={{ flexDirection: "column" }}
                  >
                    <button
                      className="btn-action approve w-full"
                      style={{ justifyContent: "center" }}
                      onClick={handleConfirmAssistance}
                      disabled={!isAssistanceConfirmed || isConfirming}
                    >
                      <CheckCircle size={18} />{" "}
                      {isConfirming
                        ? "Memproses..."
                        : "Kirim ke Tahap Validasi"}
                    </button>
                    {!isAssistanceConfirmed && (
                      <p
                        style={{
                          fontSize: "12px",
                          color: "#dc2626",
                          textAlign: "center",
                          margin: 0,
                          fontWeight: 500,
                        }}
                      >
                        {!selectedPrograms.length
                          ? "Pilih minimal satu program terlebih dahulu."
                          : "Konfirmasikan program pilihan Anda di bawah terlebih dahulu."}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}{" "}
            {/* PANEL: VALIDASI */}
            {currentTahap === "validasi" && (
              <div className="validation-panel">
                <div className="panel-header">
                  <ShieldCheck size={18} className="text-orange" />
                  <h4>Validasi</h4>
                </div>
                <div className="panel-body">
                  <div className="mb-4">
                    <label
                      style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "#6b7280",
                      }}
                    >
                      DIBUAT OLEH (ANALIS)
                    </label>
                    <p
                      style={{
                        fontSize: "14px",
                        background: "#f3f4f6",
                        padding: "10px",
                        borderRadius: "6px",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {detailData?.catatan || "Tidak ada catatan analisis yang ditambahkan."}
                    </p>
                  </div>
                  <div className="form-group">
                    <label>Catatan Supervisor / Catatan Validasi</label>
                    <textarea
                      placeholder="Masukkan catatan keputusan validasi supervisor..."
                      rows={4}
                      value={catatanSupInput}
                      onChange={(e) => setCatatanSupInput(e.target.value)}
                    ></textarea>
                  </div>
                  <div
                    className="panel-actions"
                    style={{ flexDirection: "column", gap: "8px" }}
                  >
                    <button
                      className="btn-action approve w-full"
                      style={{ justifyContent: "center" }}
                      onClick={handleSupervisorApprove}
                    >
                      <ThumbsUp size={18} /> Setujui Bantuan
                    </button>
                    <button
                      className="btn-action reject w-full"
                      style={{
                        justifyContent: "center",
                        backgroundColor: "#fff1f2",
                        color: "#be123c",
                        border: "1px solid #fda4af",
                      }}
                      onClick={handleSupervisorReject}
                    >
                      <RefreshCw size={18} /> Tolak Pengajuan
                    </button>
                  </div>
                </div>
              </div>
            )}
            {/* PANEL: DITERIMA */}
            {currentTahap === "diterima" && (
              <div className="validation-panel">
                <div
                  className="panel-header"
                  style={{ backgroundColor: "#f0fdfa" }}
                >
                  <CheckCircle
                    size={18}
                    className="text-teal"
                    style={{ color: "#0d9488" }}
                  />
                  <h4 style={{ color: "#0d9488" }}>Pengajuan Disetujui</h4>
                </div>
                <div className="panel-body">
                  <p
                    style={{
                      fontSize: "14px",
                      lineHeight: 1.5,
                      color: "#374151",
                      marginBottom: "16px",
                    }}
                  >
                    Keluarga ini telah disetujui untuk menerima program bantuan
                    sosial berikut berdasarkan analisis kebutuhan dan kelayakan
                    ekonomi desil {desil}.
                  </p>
                  
                  <div style={{ marginBottom: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>CATATAN ANALIS</label>
                      <p style={{ fontSize: "14px", background: "#f3f4f6", padding: "10px", borderRadius: "6px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                        {detailData?.catatan || "Tidak ada catatan."}
                      </p>
                    </div>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>CATATAN SUPERVISOR</label>
                      <p style={{ fontSize: "14px", background: "#f3f4f6", padding: "10px", borderRadius: "6px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                        {detailData?.catatan_supervisor || "Tidak ada catatan."}
                      </p>
                    </div>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    {selectedPrograms.map((prog) => (
                      <div
                        key={prog}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          padding: "10px",
                          background: "#f0fdf4",
                          borderRadius: "6px",
                          border: "1px solid #bbf7d0",
                          color: "#15803d",
                          fontWeight: 600,
                          fontSize: "13px",
                        }}
                      >
                        <span
                          style={{
                            display: "inline-block",
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            backgroundColor: "#16a34a",
                          }}
                        ></span>
                        {recommendations.find((r) => r.id === prog)?.title ||
                          prog}
                      </div>
                    ))}
                    {selectedPrograms.length === 0 && (
                      <div
                        style={{
                          fontSize: "13px",
                          color: "#6b7280",
                          fontStyle: "italic",
                          textAlign: "center",
                          padding: "10px",
                        }}
                      >
                        Tidak ada program bantuan spesifik yang dipilih
                      </div>
                    )}
                  </div>
                  <button
                    className="btn-action w-full"
                    style={{
                      justifyContent: "center",
                      marginTop: "16px",
                      backgroundColor: "#f8fafc",
                      border: "1px solid #e2e8f0",
                    }}
                    onClick={() => navigate("/manajemen-bantuan")}
                  >
                    Kembali ke Daftar
                  </button>
                </div>
              </div>
            )}
            {/* PANEL: DITOLAK */}
            {currentTahap === "ditolak" && (
              <div className="validation-panel">
                <div
                  className="panel-header"
                  style={{ backgroundColor: "#fef2f2" }}
                >
                  <AlertCircle
                    size={18}
                    className="text-red"
                    style={{ color: "#dc2626" }}
                  />
                  <h4 style={{ color: "#dc2626" }}>
                    Pengajuan Bantuan Ditolak
                  </h4>
                </div>
                <div className="panel-body">
                  <p
                    style={{
                      fontSize: "14px",
                      lineHeight: 1.5,
                      color: "#374151",
                      marginBottom: "16px",
                    }}
                  >
                    Berdasarkan kriteria kemiskinan dan proses verifikasi
                    supervisor, keluarga ini dinilai tidak memenuhi kriteria
                    kelayakan sebagai penerima manfaat.
                  </p>

                  <div style={{ marginBottom: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>CATATAN ANALIS</label>
                      <p style={{ fontSize: "14px", background: "#fef2f2", padding: "10px", borderRadius: "6px", whiteSpace: "pre-wrap", marginTop: "4px", color: "#b91c1c" }}>
                        {detailData?.catatan || "Tidak ada catatan."}
                      </p>
                    </div>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>CATATAN SUPERVISOR</label>
                      <p style={{ fontSize: "14px", background: "#fef2f2", padding: "10px", borderRadius: "6px", whiteSpace: "pre-wrap", marginTop: "4px", color: "#b91c1c" }}>
                        {detailData?.catatan_supervisor || "Tidak ada catatan."}
                      </p>
                    </div>
                  </div>
                  <div
                    className="panel-actions"
                    style={{ flexDirection: "column", gap: "10px" }}
                  >
                    <button
                      className="btn-action w-full"
                      style={{
                        justifyContent: "center",
                        backgroundColor: "#f3f4f6",
                        color: "#374151",
                        border: "1px solid #d1d5db",
                      }}
                      onClick={handleReanalyze}
                    >
                      <RefreshCw size={14} /> Analisis Ulang Data
                    </button>
                    <button
                      className="btn-action w-full"
                      style={{
                        justifyContent: "center",
                        backgroundColor: "#f8fafc",
                        border: "1px solid #e2e8f0",
                      }}
                      onClick={() => navigate("/manajemen-bantuan")}
                    >
                      Kembali ke Daftar
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default DetailHasil;
