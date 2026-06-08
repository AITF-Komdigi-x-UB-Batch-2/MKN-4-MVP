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
  BrainCircuit,
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

  // Parse format: "Hasil[3]{Komponen,Prediksi,Status,Alasan}:\nAtap,..."
  const parseVisualReasoning = (raw: string | null | undefined): Record<string, {prediksi: string; status: string; alasan: string}> => {
    const result: Record<string, {prediksi: string; status: string; alasan: string}> = {};
    if (!raw) return result;
    const lines = raw.split('\n').filter(l => l.trim() && !l.startsWith('Hasil['));
    for (const line of lines) {
      // Parse CSV dengan quoted strings
      const match = line.match(/^(Atap|Dinding|Lantai),([^,]+),([^,]+),"(.*)"$/i);
      if (match) {
        result[match[1].toLowerCase()] = { prediksi: match[2].trim(), status: match[3].trim(), alasan: match[4].trim() };
      }
    }
    return result;
  };
  const visualData = parseVisualReasoning(detailData?.visual_reasoning);

  // Parse AI Reasoning JSON - prioritaskan data dari server, bukan location.state
  const rawReasoning = detailData?.aiReasoning || location.state?.aiReasoning || "Data reasoning belum tersedia dari AI.";
  let ringkasanProfil = rawReasoning;
  let rekomendasiTeknis = "";
  let rekomendasiArray: any[] = [];
  try {
    const parsed = JSON.parse(rawReasoning);
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
  const [successMsg, setSuccessMsg] = useState("");
  const [isAssistanceConfirmed, setIsAssistanceConfirmed] = useState(true);
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
        if (data.catatan) {
          setCatatanSupInput(data.catatan);
        }
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
  ) => {
    console.log(`[handleUpdateStatus] Mengirim update status ke server. ID: ${id}, Status Baru: "${status}", Bantuan:`, bantuanList, `, Catatan: "${catatan}"`);
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
          }),
        },
      );
      if (!response.ok) throw new Error("Gagal update status");

      const data = await response.json();
      console.log(`[handleUpdateStatus] Sukses memperbarui status. Data terupdate:`, data);
      setDetailData(data);
      setStageState(status as Tahap);
      return true;
    } catch (e) {
      console.error(`[handleUpdateStatus] Terjadi kesalahan saat update status ID: ${id}. Error:`, e);
      return false;
    }
  };

  const handleSupervisorApprove = async () => {
    console.log(`[handleSupervisorApprove] Supervisor menyetujui bantuan sosial dengan program:`, selectedPrograms);
    const success = await handleUpdateStatus(
      "diterima",
      selectedPrograms,
      catatanSupInput,
    );
    if (success) {
      console.log(`[handleSupervisorApprove] Sukses memperbarui status menjadi diterima.`);
      setSuccessMsg("Bantuan Sosial Berhasil Disetujui!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleSupervisorReject = async () => {
    console.log(`[handleSupervisorReject] Supervisor menolak bantuan sosial.`);
    const success = await handleUpdateStatus(
      "ditolak",
      undefined,
      catatanSupInput,
    );
    if (success) {
      console.log(`[handleSupervisorReject] Sukses memperbarui status menjadi ditolak.`);
      setSuccessMsg("Pengajuan Bantuan Sosial Ditolak!");
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const handleReanalyze = async () => {
    console.log(`[handleReanalyze] Memicu analisis AI ulang untuk ID: ${id}`);
    await runAnalisisAI();
  };

  const runAnalisisAI = async () => {
    if (!id) return;
    // Kosongkan data lama agar UI terlihat fresh saat proses ulang
    setDetailData(prev => prev ? { ...prev, aiReasoning: "", rekomendasiBantuan: [], bantuan: [] } : null);
    setSelectedPrograms([]);
    setIsProcessing(true);
    try {
      const res = await apiFetch(`/api/v1/asesmen/komprehensif/${id}`, { method: "POST" });
      if (!res.ok) throw new Error("Gagal AI");
      const hasil = await res.json();
      const b = Array.isArray(hasil?.hasil_analisis_sosial_tim3?.hasil_rekomendasi_final)
        ? hasil.hasil_analisis_sosial_tim3.hasil_rekomendasi_final.filter((i: any) => i && i !== "Tidak Eligible") : [];
      await handleUpdateStatus(b.length ? "validasi" : "ditolak", b);
      setSuccessMsg("Analisis AI Selesai!");
      // Biarkan polling yang mengupdate UI - jangan setIsProcessing(false) secara manual
      // agar halaman tetap di state "proses" sampai server benar-benar selesai
    } catch (e) {
      console.error(e);
      setSuccessMsg("Gagal menjalankan Analisis AI");
      setIsProcessing(false); // hanya reset jika error
      setTimeout(() => setSuccessMsg(""), 2000);
    }
  };

  const renderCatatanView = (label: string, text: string, colorClass: string = "#f3f4f6", textColor: string = "#374151") => (
    <div style={{ marginBottom: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
      <div>
        <label style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>{label}</label>
        <p style={{ fontSize: "14px", background: colorClass, padding: "10px", borderRadius: "6px", whiteSpace: "pre-wrap", marginTop: "4px", color: textColor }}>
          {text}
        </p>
      </div>
    </div>
  );

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
                      <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                        <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#475569" }}>VARIABEL</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#475569" }}>DATA DTSEN</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#475569" }}>PREDIKSI AI</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#475569" }}>STATUS</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#475569" }}>ALASAN DETEKSI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(["atap", "dinding", "lantai"] as const).map((key, i) => {
                        const labelMap = { atap: mapAtap(detailData?.atap || 0), dinding: mapDinding(detailData?.dinding || 0), lantai: mapLantai(detailData?.lantai || 0) };
                        const namaMap = { atap: "Atap", dinding: "Dinding", lantai: "Lantai" };
                        const vis = visualData[key];
                        const isSesuai = vis?.status?.toLowerCase() === "sesuai";
                        return (
                          <tr key={key} style={{ borderBottom: i < 2 ? "1px solid #e2e8f0" : undefined }}>
                            <td style={{ padding: "14px 16px", fontWeight: 600, color: "#1e293b" }}>{namaMap[key]}</td>
                            <td style={{ padding: "14px 16px", color: "#475569" }}>{labelMap[key]}</td>
                            <td style={{ padding: "14px 16px", fontWeight: 600, color: vis ? (isSesuai ? "#10b981" : "#ef4444") : "#94a3b8" }}>
                              {vis ? vis.prediksi : "-"}
                            </td>
                            <td style={{ padding: "14px 16px" }}>
                              {vis ? (
                                <span style={{ padding: "3px 10px", borderRadius: 9999, fontSize: 11, fontWeight: 700,
                                  backgroundColor: isSesuai ? "#f0fdf4" : "#fef2f2",
                                  color: isSesuai ? "#16a34a" : "#dc2626",
                                  border: `1px solid ${isSesuai ? "#bbf7d0" : "#fca5a5"}` }}>
                                  {vis.status}
                                </span>
                              ) : renderVisualMatchBadge(null)}
                            </td>
                            <td style={{ padding: "14px 16px", color: "#475569", fontSize: 12, lineHeight: 1.5 }}>
                              {vis ? vis.alasan : "-"}
                            </td>
                          </tr>
                        );
                      })}
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
                  <div
                    className="panel-actions"
                    style={{ flexDirection: "column" }}
                  >
                    <button
                      className="btn-action w-full"
                      style={{
                        justifyContent: "center",
                        backgroundColor: "#f0fdf4",
                        color: "#166534",
                        border: "1px solid #bbf7d0",
                      }}
                      onClick={runAnalisisAI}
                      disabled={isProcessing}
                    >
                      <BrainCircuit size={18} />{" "}
                      {isProcessing ? "AI Memproses..." : "Jalankan Analisis AI"}
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
                  <div className="form-group">
                    <label>Catatan</label>
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
                  {renderCatatanView("CATATAN", detailData?.catatan || "Tidak ada catatan.")}
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
                  {renderCatatanView("CATATAN PEMBERI BANTUAN", detailData?.catatan || "Tidak ada catatan.", "#fef2f2", "#b91c1c")}
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
