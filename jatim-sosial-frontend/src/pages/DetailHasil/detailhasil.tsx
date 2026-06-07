import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { apiFetch } from "../../services/api";
import type { Tahap } from "../../data/mockData";
import AdminLayout from "../../components/layout/AdminLayout";
import { RecommendationCard, type RecommendationData } from "../../components/cards/RecommendationCard";
import {
  User,
  Home,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  ThumbsUp,
  RefreshCw,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
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
  skorPKHPlus: number;
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
  const map: Record<number, string> = {
    1: "Beton",
    2: "Genteng Tanah Liat",
    3: "Asbes",
    4: "Seng",
    5: "Bambu",
    6: "Jerami/Ijuk",
    7: "Lainnya",
  };
  return map[val] || "Tidak Diketahui";
};

const mapDinding = (val: number) => {
  const map: Record<number, string> = {
    1: "Tembok",
    2: "Kayu",
    3: "Bambu",
    4: "Tanah",
    5: "Lainnya",
  };
  return map[val] || "Tidak Diketahui";
};

const mapLantai = (val: number) => {
  const map: Record<number, string> = {
    1: "Marmer/Granit",
    2: "Keramik",
    3: "Ubin/Semen",
    4: "Kayu",
    5: "Bambu",
    6: "Tanah",
    7: "Lainnya",
  };
  return map[val] || "Tidak Diketahui";
};

const DetailHasil: React.FC<DetailHasilProps> = ({ onLogout }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [detailData, setDetailData] = useState<DetailKeluargaResponse | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);

  const familyId = id || location.state?.id_keluarga;

  // Parse AI Reasoning JSON
  let ringkasanProfil = location.state?.aiReasoning || "Data reasoning belum tersedia dari AI.";
  let rekomendasiTeknis = "";
  let rekomendasiArray: any[] = [];
  try {
    const parsed = JSON.parse(ringkasanProfil);
    if (parsed.ringkasan_profil) {
      ringkasanProfil = parsed.ringkasan_profil;
    }
    if (parsed.rekomendasi_teknis) {
      rekomendasiTeknis = parsed.rekomendasi_teknis;
    }
    if (parsed.rekomendasi && Array.isArray(parsed.rekomendasi)) {
      rekomendasiArray = parsed.rekomendasi;
    }
  } catch (e) {
    // Jika bukan JSON (format lama), biarkan menggunakan string asli
  }

  const getAIReason = (prog: string, defaultReason: string) => {
    const rec = rekomendasiArray.find((r: any) => r.nama_program && r.nama_program.toUpperCase().includes(prog.toUpperCase()));
    if (rec && rec.alasan_kelayakan) return rec.alasan_kelayakan;
    return rekomendasiTeknis || defaultReason;
  };

  const [stageState, setStageState] = useState<Tahap>(
    location.state?.tahap || "analisis",
  );
  const [selectedPrograms, setSelectedPrograms] = useState<string[]>(
    location.state?.bantuan || [],
  );
  const [isConfirming, setIsConfirming] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [isAssistanceConfirmed, setIsAssistanceConfirmed] = useState(true);
  const [catatanInput, setCatatanInput] = useState("");
  const [catatanSupInput, setCatatanSupInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const latestRequestRef = React.useRef(0);

  const displayImages = (() => {
    const urls = [...(detailData?.foto_urls || [])];

    // Replace minio hostnames if needed
    const processedUrls = urls.map((url) =>
      url.replace(
        "http://minio:9000",
        `http://${window.location.hostname}:9000`,
      ),
    );

    // If there is only one photo or it's empty, and we have a url_foto
    if (processedUrls.length === 0 && detailData?.url_foto) {
      processedUrls.push(
        detailData.url_foto.replace(
          "http://minio:9000",
          `http://${window.location.hostname}:9000`,
        ),
      );
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

  const fetchDetail = useCallback(async () => {
    if (!familyId) return;
    const requestId = ++latestRequestRef.current;

    try {
      const res = await apiFetch(`/api/v1/manajemen-bantuan/${familyId}`);
      if (requestId !== latestRequestRef.current) return;

      if (res.status === 409) {
        setIsProcessing(true);
        setStageState("proses");
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setDetailData(data);
        setIsProcessing(false);

        setStageState(data.tahap);
        setSelectedPrograms(data.bantuan && data.bantuan.length > 0 ? data.bantuan : (data.rekomendasiBantuan || []));
        setIsAssistanceConfirmed(true);
        if (data.catatan) setCatatanInput(data.catatan);
        if (data.catatan_supervisor)
          setCatatanSupInput(data.catatan_supervisor);
      }
    } catch (err) {
      if (requestId === latestRequestRef.current) {
        console.error("Gagal mengambil data detail", err);
      }
    } finally {
      if (requestId === latestRequestRef.current) {
        setIsLoading(false);
      }
    }
  }, [familyId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  useEffect(() => {
    if (!isProcessing) return;

    const pollInterval = setInterval(() => {
      fetchDetail();
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [fetchDetail, isProcessing]);

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
    pkh_plus: detailData?.skorPKHPlus || 0,
  };

  const getAtapVisual = () => {
    if (detailData?.visual_match === undefined || detailData?.visual_match === null) {
      return "-";
    }
    if (detailData.visual_match) {
      return mapAtap(detailData.atap || 0);
    }
    if (detailData.atap === 1 || detailData.atap === 2) {
      return "Seng";
    }
    return "Jerami/Ijuk";
  };

  const getDindingVisual = () => {
    if (detailData?.visual_match === undefined || detailData?.visual_match === null) {
      return "-";
    }
    if (detailData.visual_match) {
      return mapDinding(detailData.dinding || 0);
    }
    if (detailData.dinding === 1 || detailData.dinding === 2) {
      return "Bambu";
    }
    return "Bambu/Seng Bekas";
  };

  const getLantaiVisual = () => {
    if (detailData?.visual_match === undefined || detailData?.visual_match === null) {
      return "-";
    }
    if (detailData.visual_match) {
      return mapLantai(detailData.lantai || 0);
    }
    if (detailData.lantai === 1 || detailData.lantai === 2) {
      return "Ubin/Semen";
    }
    return "Tanah";
  };

  const recommendations: RecommendationData[] = [
    {
      id: "ASPD",
      title: "ASPD (Asistensi Sosial Penyandang Disabilitas)",
      match: familyScores.aspd,
      desc: "Bantuan sosial tunai dari Pemerintah Provinsi Jawa Timur untuk penyandang disabilitas berat guna memenuhi kebutuhan dasar dan meningkatkan kualitas hidup mereka.",
      isReceived: false,
    },
    {
      id: "PKH Plus",
      title: "PKH Plus (Program Keluarga Harapan Plus)",
      match: familyScores.pkh_plus,
      desc: "Bantuan sosial bersyarat berupa dana tunai khusus bagi lanjut usia (lansia) berusia 70 tahun ke atas dari keluarga sangat miskin yang terdaftar dalam DTKS.",
      isReceived: false,
    },
  ];

  const familyRecs = detailData?.rekomendasiBantuan || [];

  const filteredRecommendations = recommendations.filter((rec) => {
    return familyRecs.includes(rec.id);
  });

  const handleToggleProgram = (id: string) => {
    if (isFinalized || isAssistanceConfirmed) return;

    setSelectedPrograms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  const handleUpdateStatus = async (
    status: string,
    bantuanList?: string[],
    catatan?: string,
    catatan_supervisor?: string,
  ) => {
    try {
      const response = await apiFetch(
        `/api/v1/manajemen-bantuan/${id}/status`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            status_validasi: status,
            bantuan: bantuanList,
            catatan: catatan,
            catatan_supervisor: catatan_supervisor,
          }),
        },
      );
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
    const success = await handleUpdateStatus(
      "validasi",
      selectedPrograms,
      catatanInput,
    );
    setIsConfirming(false);
    if (success) {
      setSuccessMsg("Rekomendasi bantuan berhasil diajukan ke tahap Validasi!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleSupervisorApprove = async () => {
    const success = await handleUpdateStatus(
      "diterima",
      selectedPrograms,
      undefined,
      catatanSupInput,
    );
    if (success) {
      setSuccessMsg("Bantuan Sosial Berhasil Disetujui!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleSupervisorReject = async () => {
    const success = await handleUpdateStatus(
      "ditolak",
      undefined,
      undefined,
      catatanSupInput,
    );
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

  if (isProcessing || currentTahap === "proses") {
    return (
      <AdminLayout title="Detail Analisis" onLogout={onLogout}>
        <div className="flex items-center justify-center h-full">
          <p>Data sedang diproses. Silakan coba lagi beberapa saat.</p>
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
                          maxWidth:
                            displayImages.length > 1 ? "360px" : "500px",
                        }}
                      >
                        <div
                          className="placeholder-image"
                          style={{
                            overflow: "hidden",
                            position: "relative",
                            height: "240px",
                          }}
                        >
                          <img
                            src={imgUrl}
                            alt={`Survey Hunian ${index === 0 ? "Tampak Luar" : "Tampak Dalam"}`}
                            style={{
                              width: "100%",
                              height: "100%",
                              objectFit: "cover",
                            }}
                          />
                          <div
                            style={{
                              position: "absolute",
                              bottom: 10,
                              left: "50%",
                              transform: "translateX(-50%)",
                              background: "rgba(0,0,0,0.65)",
                              color: "white",
                              padding: "4px 10px",
                              borderRadius: 12,
                              fontSize: 12,
                              fontWeight: 600,
                              whiteSpace: "nowrap",
                            }}
                          >
                            {index === 0
                              ? "Foto 1: Tampak Luar"
                              : "Foto 2: Tampak Dalam"}
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
                          PREDIKSI AI
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
                          <span style={{
                            fontWeight: 600,
                            color: detailData?.visual_match === undefined || detailData?.visual_match === null
                              ? "#64748b"
                              : detailData.visual_match
                                ? "#10b981"
                                : "#ef4444"
                          }}>
                            {getAtapVisual()}
                          </span>
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
                          <span style={{
                            fontWeight: 600,
                            color: detailData?.visual_match === undefined || detailData?.visual_match === null
                              ? "#64748b"
                              : detailData.visual_match
                                ? "#10b981"
                                : "#ef4444"
                          }}>
                            {getDindingVisual()}
                          </span>
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          {renderVisualMatchBadge(detailData?.visual_match)}
                        </td>
                        <td style={{ padding: "14px 16px", color: "#475569" }}>
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
                          <span style={{
                            fontWeight: 600,
                            color: detailData?.visual_match === undefined || detailData?.visual_match === null
                              ? "#64748b"
                              : detailData.visual_match
                                ? "#10b981"
                                : "#ef4444"
                          }}>
                            {getLantaiVisual()}
                          </span>
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
                <h4>Ringkasan Singkat</h4>
              </div>
              <div
                className="detail-card-body"
                style={{
                  lineHeight: "1.6",
                  color: "#4a5568",
                  fontSize: "14px",
                  display: "flex",
                  flexDirection: "column"
                }}
              >
                {filteredRecommendations.length > 0 ? (
                  <div>
                    {filteredRecommendations.map(rec => {
                      const reasonText = getAIReason(rec.id, "");
                      if (!reasonText) return null;
                      return (
                        <div key={rec.id} style={{ marginBottom: "12px" }}>
                          <strong style={{ color: "#334155" }}>Alasan kelayakan {rec.id}:</strong>
                          <div style={{ marginTop: "4px" }}>
                            <ReactMarkdown>{reasonText}</ReactMarkdown>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div>
                    <strong style={{ color: "#334155" }}>Analisis Keseluruhan:</strong>
                    <div style={{ marginTop: "4px" }}>
                      <ReactMarkdown>{ringkasanProfil}</ReactMarkdown>
                    </div>
                    {rekomendasiTeknis && (
                      <div style={{ marginTop: "12px" }}>
                        <strong style={{ color: "#334155" }}>Rekomendasi Teknis:</strong>
                        <div style={{ marginTop: "4px" }}>
                          <ReactMarkdown>{rekomendasiTeknis}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Smart Recommendations Section */}
            {currentTahap !== "diterima" && (
              <div className="detail-card-section">
                <div className="detail-card-header">
                  <h4>Bantuan yang Eligible (Analisis AI)</h4>
                </div>
                <div className="detail-card-body">
                  <div className="recommendation-cards-grid">
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
                          program ASPD, PKH+, atau KE.
                        </p>
                      </div>
                    ) : (
                      filteredRecommendations.map((rec) => {
                        const enhancedRec = {
                          ...rec,
                          reason: ""
                        };
                        return (
                          <div key={rec.id} style={{ marginBottom: "24px" }}>
                            <RecommendationCard
                              data={enhancedRec}
                              isSelected={selectedPrograms.includes(rec.id)}
                              isLocked={isFinalized || isAssistanceConfirmed}
                              onToggle={handleToggleProgram}
                            />
                            {rekomendasiTeknis && (
                              <div style={{ marginTop: "16px", padding: "16px", backgroundColor: "#f0f9ff", borderRadius: "8px", border: "1px solid #bae6fd", color: "#0369a1", fontSize: "14px", lineHeight: "1.6" }}>
                                <strong style={{ display: "block", marginBottom: "8px", color: "#0284c7" }}>Spesifikasi Teknis:</strong>
                                <ReactMarkdown>{rekomendasiTeknis}</ReactMarkdown>
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
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
                      disabled={selectedPrograms.length === 0 || isConfirming}
                    >
                      <CheckCircle size={18} />{" "}
                      {isConfirming
                        ? "Memproses..."
                        : "Kirim ke Tahap Validasi"}
                    </button>
                    {selectedPrograms.length === 0 && (
                      <p
                        style={{
                          fontSize: "12px",
                          color: "#dc2626",
                          textAlign: "center",
                          margin: 0,
                          fontWeight: 500,
                        }}
                      >
                        Tidak ada bantuan eligible untuk warga ini.
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
                      {detailData?.catatan ||
                        "Tidak ada catatan analisis yang ditambahkan."}
                    </p>
                  </div>
                  <div className="form-group">
                    <label>Catatan Supervisor</label>
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

                  <div
                    style={{
                      marginBottom: "24px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <label
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "#6b7280",
                        }}
                      >
                        CATATAN ANALIS
                      </label>
                      <p
                        style={{
                          fontSize: "14px",
                          background: "#f3f4f6",
                          padding: "10px",
                          borderRadius: "6px",
                          whiteSpace: "pre-wrap",
                          marginTop: "4px",
                        }}
                      >
                        {detailData?.catatan || "Tidak ada catatan."}
                      </p>
                    </div>
                    <div>
                      <label
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "#6b7280",
                        }}
                      >
                        CATATAN SUPERVISOR
                      </label>
                      <p
                        style={{
                          fontSize: "14px",
                          background: "#f3f4f6",
                          padding: "10px",
                          borderRadius: "6px",
                          whiteSpace: "pre-wrap",
                          marginTop: "4px",
                        }}
                      >
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
                  <div
                    className="panel-actions"
                    style={{ flexDirection: "column", gap: "10px", marginTop: "16px" }}
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

                  <div
                    style={{
                      marginBottom: "24px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <label
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "#6b7280",
                        }}
                      >
                        CATATAN ANALIS
                      </label>
                      <p
                        style={{
                          fontSize: "14px",
                          background: "#fef2f2",
                          padding: "10px",
                          borderRadius: "6px",
                          whiteSpace: "pre-wrap",
                          marginTop: "4px",
                          color: "#b91c1c",
                        }}
                      >
                        {detailData?.catatan || "Tidak ada catatan."}
                      </p>
                    </div>
                    <div>
                      <label
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "#6b7280",
                        }}
                      >
                        CATATAN SUPERVISOR
                      </label>
                      <p
                        style={{
                          fontSize: "14px",
                          background: "#fef2f2",
                          padding: "10px",
                          borderRadius: "6px",
                          whiteSpace: "pre-wrap",
                          marginTop: "4px",
                          color: "#b91c1c",
                        }}
                      >
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
