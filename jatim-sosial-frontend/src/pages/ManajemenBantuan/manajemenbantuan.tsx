import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "../../components/layout/AdminLayout";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  FileBarChart,
  CheckCircle,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Loader2,
  ShieldCheck,
  BrainCircuit,
  CheckSquare,
  Square,
  XCircle,
} from "lucide-react";
import LoadingState from "../../components/ui/LoadingState";
import EmptyState from "../../components/ui/EmptyState";
import { type Tahap, type AnalisisOutput } from "../../data/mockData";
import { apiFetch } from "../../services/api";
import "./ManajemenBantuan.css";

/* ─── Types ──────────────────────────────── */

export interface DataRow extends AnalisisOutput {
  nama: string;
  nik: string;
  wilayah: string;
  kecamatan: string;
  desil: number;
  skorASPD: number;
  skorPKHT: number;
}

// DataRow kini didefinisikan secara independen karena data asli berasal dari backend

interface ManajemenBantuanProps {
  onLogout?: () => void;
}

type TabKey = "semua" | Tahap;
type SortKey =
  | "id"
  | "nama"
  | "wilayah"
  | "desil"
  | "tahap"
  | "bantuan"
  | "perubahanDesil"
  | "skorASPD"
  | "skorPKHT";

/* ─── Helpers ────────────────────────────── */

const TABS: { key: TabKey; label: string; dotColor: string }[] = [
  { key: "semua", label: "Semua", dotColor: "#6b7280" },
  { key: "proses", label: "Diproses", dotColor: "#94a3b8" },
  { key: "analisis", label: "Analisis", dotColor: "#3b82f6" },
  { key: "validasi", label: "Perlu Validasi", dotColor: "#f97316" },
  { key: "diterima", label: "Diterima", dotColor: "#10b981" },
  { key: "ditolak", label: "Ditolak", dotColor: "#ef4444" },
];

const getDesilColor = (desil: number) => {
  if (desil <= 3) return "red";
  if (desil <= 6) return "orange";
  return "green";
};

const getStageBadgeClass = (tahap: Tahap) => {
  switch (tahap) {
    case "proses":
      return "mb-badge-proses";
    case "analisis":
      return "mb-badge-analisis";
    case "validasi":
      return "mb-badge-validasi";
    case "diterima":
      return "mb-badge-aktif";
    case "ditolak":
      return "mb-badge-selesai";
  }
};

const getStageBadgeLabel = (tahap: Tahap) => {
  switch (tahap) {
    case "proses":
      return "Diproses";
    case "analisis":
      return "Analisis";
    case "validasi":
      return "Validasi";
    case "diterima":
      return "Diterima";
    case "ditolak":
      return "Ditolak";
  }
};

const getEmptyMessage = (tab: TabKey) => {
  switch (tab) {
    case "semua":
      return "Belum ada data bantuan untuk ditampilkan.";
    case "proses":
      return "Tidak ada data yang sedang diproses.";
    case "analisis":
      return "Tidak ada riwayat analisis pada periode ini.";
    case "validasi":
      return "Tidak ada permohonan yang menunggu validasi.";
    case "diterima":
      return "Tidak ada bantuan yang disetujui saat ini.";
    case "ditolak":
      return "Tidak ada pengajuan bantuan yang ditolak.";
  }
};

/* ─── Component ──────────────────────────── */

const ManajemenBantuan: React.FC<ManajemenBantuanProps> = ({ onLogout }) => {
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState<TabKey>("semua");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("Semua");
  const [filterWilayah, setFilterWilayah] = useState("Semua");
  const [filterBantuan, setFilterBantuan] = useState("Semua");
  const [sortConfig, setSortConfig] = useState<{
    key: SortKey;
    direction: "asc" | "desc";
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [data, setData] = useState<DataRow[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);

  const fetchData = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setIsLoading(true);
      const res = await apiFetch("/api/v1/manajemen-bantuan");
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Gagal mengambil data dari server:", e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const hasProcessingData = data.some((row) => row.tahap === "proses");
    setIsMonitoring(hasProcessingData);

    if (!hasProcessingData) return;

    const pollInterval = setInterval(() => {
      fetchData();
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [data, fetchData]);

  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, searchTerm, filterStatus, filterWilayah, filterBantuan]);

  // Counts per tab (before search/filter)
  const tabCounts = useMemo(
    () => ({
      semua: data.length,
      proses: data.filter((d) => d.tahap === "proses").length,
      analisis: data.filter((d) => d.tahap === "analisis").length,
      validasi: data.filter((d) => d.tahap === "validasi").length,
      diterima: data.filter((d) => d.tahap === "diterima").length,
      ditolak: data.filter((d) => d.tahap === "ditolak").length,
    }),
    [data],
  );

  // Filtered data
  const filteredData = useMemo(() => {
    let result = data;

    // Tab filter
    if (activeTab !== "semua") {
      result = result.filter((d) => d.tahap === activeTab);
    }

    // Search
    if (searchTerm) {
      const lower = searchTerm.toLowerCase();
      result = result.filter(
        (d) =>
          d.nama.toLowerCase().includes(lower) ||
          d.nik.includes(lower) ||
          d.idLabel.toLowerCase().includes(lower),
      );
    }

    // Status filter (maps to tahap)
    if (filterStatus !== "Semua") {
      const mapping: Record<string, Tahap> = {
        Diproses: "proses",
        Analisis: "analisis",
        Validasi: "validasi",
        Diterima: "diterima",
        Ditolak: "ditolak",
      };
      if (mapping[filterStatus]) {
        result = result.filter((d) => d.tahap === mapping[filterStatus]);
      }
    }

    // Wilayah filter
    if (filterWilayah !== "Semua") {
      result = result.filter((d) => d.wilayah === filterWilayah);
    }

    // Bantuan filter
    if (filterBantuan !== "Semua") {
      result = result.filter(
        (d) => d.bantuan && d.bantuan.includes(filterBantuan),
      );
    }

    // Sort ascending by skorKesejahteraan to show lowest welfare first
    result.sort((a, b) => a.skorKesejahteraan - b.skorKesejahteraan);

    // Generic Sort
    if (sortConfig) {
      result.sort((a, b) => {
        let valA: any = a[sortConfig.key as keyof DataRow];
        let valB: any = b[sortConfig.key as keyof DataRow];

        const tahapOrder: Record<string, number> = {
          proses: 0,
          analisis: 1,
          validasi: 2,
          diterima: 3,
          ditolak: 4,
        };

        if (sortConfig.key === "id") {
          valA = a.idLabel;
          valB = b.idLabel;
        } else if (sortConfig.key === "bantuan") {
          valA = a.bantuan ? a.bantuan.join(", ") : "";
          valB = b.bantuan ? b.bantuan.join(", ") : "";
        } else if (sortConfig.key === "perubahanDesil") {
          valA = (a.desilSesudah ?? 0) - (a.desilSebelum ?? 0);
          valB = (b.desilSesudah ?? 0) - (b.desilSebelum ?? 0);
        } else if (sortConfig.key === "tahap") {
          valA = tahapOrder[a.tahap] || 99;
          valB = tahapOrder[b.tahap] || 99;
        } else if (sortConfig.key === "skorASPD") {
          valA = a.skorASPD;
          valB = b.skorASPD;
        } else if (sortConfig.key === "skorPKHT") {
          valA = a.skorPKHT;
          valB = b.skorPKHT;
        }

        if (typeof valA === "string" && typeof valB === "string") {
          return sortConfig.direction === "asc"
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA);
        } else {
          return sortConfig.direction === "asc"
            ? valA > valB
              ? 1
              : valA < valB
                ? -1
                : 0
            : valB > valA
              ? 1
              : valB < valA
                ? -1
                : 0;
        }
      });
    }

    return result;
  }, [
    data,
    activeTab,
    searchTerm,
    filterStatus,
    filterWilayah,
    filterBantuan,
    sortConfig,
  ]);

  // Pagination
  const totalPages = Math.max(
    1,
    Math.ceil(filteredData.length / ITEMS_PER_PAGE),
  );
  const paginatedData = filteredData.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  );

  const getPageNumbers = () => {
    const pages: (number | "...")[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }
    return pages;
  };

  // Actions
  const runAnalisisAndAdvance = async (id: string) => {
    const res = await apiFetch("/api/v1/asesmen/sosial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keluarga_id: id }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Gagal menjalankan analisis.");
    }

    const hasil = await res.json().catch(() => ({}));
    const bantuan = Array.isArray(hasil?.hasil_rekomendasi_final)
      ? hasil.hasil_rekomendasi_final
      : [];

    const resUpdate = await apiFetch(`/api/v1/manajemen-bantuan/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status_validasi: "validasi",
        bantuan,
      }),
    });
    if (!resUpdate.ok) {
      const err = await resUpdate.json().catch(() => ({}));
      throw new Error(err.detail || "Gagal memindahkan ke tahap validasi.");
    }
  };

  const handleAnalisis = async (id: string) => {
    setAnalyzingId(id);
    try {
      await runAnalisisAndAdvance(id);
      await fetchData(); // refresh data setelah AI selesai
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzingId(null);
    }
  };

  // Batch selection helpers
  const analisisRows = paginatedData.filter((r) => r.tahap === "analisis");
  const allAnalisisSelected =
    analisisRows.length > 0 &&
    analisisRows.every((r) => selectedRows.has(r.id_keluarga));

  const toggleRowSelection = (id: string) => {
    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAllAnalisis = () => {
    if (allAnalisisSelected) {
      setSelectedRows((prev) => {
        const next = new Set(prev);
        analisisRows.forEach((r) => next.delete(r.id_keluarga));
        return next;
      });
    } else {
      setSelectedRows((prev) => {
        const next = new Set(prev);
        analisisRows.forEach((r) => next.add(r.id_keluarga));
        return next;
      });
    }
  };

  const handleBatchAnalisis = async () => {
    if (selectedRows.size === 0 || isBatchAnalyzing) return;
    setIsBatchAnalyzing(true);
    setBatchProgress(0);
    const ids = Array.from(selectedRows);
    const total = ids.length;
    let processed = 0;

    for (const id of ids) {
      try {
        await runAnalisisAndAdvance(id);
      } catch (e) {
        console.error(e);
      }
      processed++;
      setBatchProgress(Math.round((processed / total) * 100));
    }

    await fetchData();
    setIsBatchAnalyzing(false);
    setSelectedRows(new Set());
    setBatchProgress(0);
  };

  const handleAnalisisAll = async () => {
    const allAnalisis = data.filter((d) => d.tahap === "analisis");
    if (allAnalisis.length === 0 || isBatchAnalyzing) return;
    const allIds = new Set(allAnalisis.map((d) => d.id_keluarga));
    setSelectedRows(allIds);
    setIsBatchAnalyzing(true);
    setBatchProgress(0);
    const ids = Array.from(allIds);
    const total = ids.length;
    let processed = 0;

    for (const id of ids) {
      try {
        await runAnalisisAndAdvance(id);
      } catch (e) {
        console.error(e);
      }
      processed++;
      setBatchProgress(Math.round((processed / total) * 100));
    }

    await fetchData();
    setIsBatchAnalyzing(false);
    setSelectedRows(new Set());
    setBatchProgress(0);
  };

  const resetFilters = () => {
    setSearchTerm("");
    setFilterStatus("Semua");
    setFilterWilayah("Semua");
    setFilterBantuan("Semua");
    setSortConfig(null);
  };

  const handleSort = (key: SortKey) => {
    let direction: "asc" | "desc" = "asc";
    if (sortConfig && sortConfig.key === key) {
      direction = sortConfig.direction === "asc" ? "desc" : "asc";
    }
    setSortConfig({ key, direction });
  };

  const renderSortHeader = (label: string, sortKey: SortKey) => {
    const isActive = sortConfig?.key === sortKey;
    return (
      <th
        className="mb-th-sortable"
        onClick={() => handleSort(sortKey)}
        title={`Klik untuk mengurutkan berdasarkan ${label.toLowerCase()}`}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {label}
          <span className={`mb-sort-icon ${isActive ? "active" : ""}`}>
            {isActive && sortConfig.direction === "asc" ? (
              <ChevronUp size={14} />
            ) : isActive && sortConfig.direction === "desc" ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronsUpDown size={14} />
            )}
          </span>
        </div>
      </th>
    );
  };

  // Determine what columns to show
  const showBantuan = activeTab !== "analisis";
  const showStageBadge = true;
  const showDesilChange = false; // Evaluasi kaku telah dihilangkan

  const colCount =
    1 + // checkbox
    5 + // id, nama, wilayah, desil
    2 + // ASPD and PKHT columns
    (showStageBadge ? 1 : 0) +
    (showBantuan ? 1 : 0) +
    (showDesilChange ? 1 : 0) +
    1; // aksi

  return (
    <AdminLayout title="Manajemen Bantuan" onLogout={onLogout}>
      <div className="mb-page-wrapper">
        {/* ── Header ────────────────────────── */}
        <div className="mb-header">
          <div className="mb-title-area">
            <h3>Manajemen Bantuan</h3>
            <p>
              Kelola seluruh rekomendasi bantuan sosial mulai dari tahap
              analisis, validasi, hingga penetapan diterima/ditolak.
            </p>
          </div>
          <div className="mb-actions">
            {isMonitoring && (
              <div className="mb-monitoring-status">
                <Loader2 size={14} className="mb-spin" />
                Memantau data diproses
              </div>
            )}
            <button
              className="mb-btn-primary"
              onClick={handleAnalisisAll}
              disabled={
                isBatchAnalyzing ||
                data.filter((d) => d.tahap === "analisis").length === 0
              }
              style={{
                opacity:
                  data.filter((d) => d.tahap === "analisis").length === 0
                    ? 0.5
                    : 1,
              }}
            >
              <BrainCircuit size={16} /> Analisis Semua (
              {data.filter((d) => d.tahap === "analisis").length})
            </button>
          </div>
        </div>

        {/* ── Tab Navigation ────────────────── */}
        <div className="mb-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`mb-tab-item ${activeTab === tab.key ? "active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
              disabled={isLoading}
            >
              <span
                className="mb-tab-dot"
                style={{ backgroundColor: tab.dotColor }}
              />
              {tab.label}
              <span className="mb-tab-count">{tabCounts[tab.key]}</span>
            </button>
          ))}
        </div>

        {/* ── Filter & Search ───────────────── */}
        <div className="mb-filter-bar">
          <div className="mb-search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Cari Nama / NIK / ID Analisis..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="mb-filter-group">
            <label>STATUS</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              disabled={isLoading}
            >
              <option value="Semua">Semua Status</option>
              <option value="Diproses">Diproses</option>
              <option value="Analisis">Analisis</option>
              <option value="Validasi">Validasi</option>
              <option value="Diterima">Diterima</option>
              <option value="Ditolak">Ditolak</option>
            </select>
          </div>

          <div className="mb-filter-group">
            <label>WILAYAH</label>
            <select
              value={filterWilayah}
              onChange={(e) => setFilterWilayah(e.target.value)}
              disabled={isLoading}
            >
              <option value="Semua">Semua Wilayah</option>
              <option value="Malang">Malang</option>
            </select>
          </div>

          <div className="mb-filter-group">
            <label>JENIS BANTUAN</label>
            <select
              value={filterBantuan}
              onChange={(e) => setFilterBantuan(e.target.value)}
              disabled={isLoading}
            >
              <option value="Semua">Semua Jenis</option>
              <option value="ASPD">ASPD</option>
              <option value="PKHT">PKHT</option>
              <option value="KE">KE</option>
              <option value="JAWARA">Jawara</option>
              <option value="JAWARA P">Jawara P</option>
              <option value="PPU">PPU</option>
            </select>
          </div>

          <div className="mb-filter-group">
            <label>URUTKAN</label>
            <select
              value={
                sortConfig
                  ? `${sortConfig.key}-${sortConfig.direction}`
                  : "default"
              }
              onChange={(e) => {
                if (e.target.value === "default") {
                  setSortConfig(null);
                } else {
                  const [key, direction] = e.target.value.split("-");
                  setSortConfig({
                    key: key as SortKey,
                    direction: direction as "asc" | "desc",
                  });
                }
              }}
              disabled={isLoading}
            >
              <option value="default">Default</option>
              <option value="skorASPD-desc">Skor ASPD Tertinggi</option>
              <option value="skorPKHT-desc">Skor PKHT Tertinggi</option>
              <option value="nama-asc">Nama (A - Z)</option>
            </select>
          </div>

          <button
            className="mb-btn-reset"
            onClick={resetFilters}
            disabled={isLoading}
          >
            Reset Filter
          </button>
        </div>

        {/* ── Data Table ────────────────────── */}
        <div className="mb-table-card">
          <div className="mb-table-responsive">
            <table className="mb-table">
              <thead>
                <tr>
                  <th
                    style={{
                      width: "44px",
                      textAlign: "center",
                      padding: "14px 8px",
                    }}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelectAllAnalisis();
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        margin: "0 auto",
                      }}
                      title={
                        allAnalisisSelected
                          ? "Batal pilih semua"
                          : "Pilih semua analisis"
                      }
                    >
                      {allAnalisisSelected ? (
                        <CheckSquare size={16} style={{ color: "#2563eb" }} />
                      ) : (
                        <Square size={16} style={{ color: "#9ca3af" }} />
                      )}
                    </button>
                  </th>
                  {renderSortHeader("ID / TANGGAL", "id")}
                  {renderSortHeader("NAMA PENERIMA", "nama")}
                  {renderSortHeader("WILAYAH", "wilayah")}
                  {renderSortHeader("DESIL", "desil")}
                  {renderSortHeader("ASPD", "skorASPD")}
                  {renderSortHeader("PKHT", "skorPKHT")}
                  {showStageBadge && renderSortHeader("STATUS TAHAP", "tahap")}
                  {showBantuan && renderSortHeader("BANTUAN", "bantuan")}
                  {showDesilChange &&
                    renderSortHeader("PERUBAHAN DESIL", "perubahanDesil")}
                  <th style={{ textAlign: "center" }}>AKSI</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={colCount} style={{ padding: 0 }}>
                      <LoadingState />
                    </td>
                  </tr>
                ) : filteredData.length === 0 ? (
                  <tr>
                    <td colSpan={colCount} style={{ padding: 0 }}>
                      <EmptyState
                        title="Tidak ada data pada tahap ini"
                        description={getEmptyMessage(activeTab)}
                        onReset={resetFilters}
                      />
                    </td>
                  </tr>
                ) : (
                  paginatedData.map((row) => (
                    <tr
                      key={row.id_keluarga}
                      onClick={() =>
                        navigate(`/detail-hasil/${row.id_keluarga}`, {
                          state: row,
                        })
                      }
                      className={`mb-clickable-row ${selectedRows.has(row.id_keluarga) ? "mb-row-selected" : ""}`}
                    >
                      {/* Checkbox */}
                      <td
                        style={{
                          width: "44px",
                          textAlign: "center",
                          padding: "14px 8px",
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {row.tahap === "analisis" ? (
                          <button
                            onClick={() => toggleRowSelection(row.id_keluarga)}
                            style={{
                              background: "none",
                              border: "none",
                              cursor: "pointer",
                              padding: 0,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              margin: "0 auto",
                            }}
                          >
                            {selectedRows.has(row.id_keluarga) ? (
                              <CheckSquare
                                size={16}
                                style={{ color: "#2563eb" }}
                              />
                            ) : (
                              <Square size={16} style={{ color: "#cbd5e1" }} />
                            )}
                          </button>
                        ) : (
                          <span
                            style={{
                              display: "inline-block",
                              width: 16,
                              height: 16,
                            }}
                          />
                        )}
                      </td>
                      {/* ID / Tanggal */}
                      <td>
                        <div
                          className="mb-cell-link"
                          style={{ display: "inline-block" }}
                        >
                          {row.idLabel}
                        </div>
                        <div className="mb-cell-secondary">{row.tanggal}</div>
                      </td>

                      {/* Nama */}
                      <td>
                        <div className="mb-cell-primary">{row.nama}</div>
                        <div className="mb-cell-secondary">
                          NIK:{" "}
                          {row.nik.length > 20
                            ? row.nik.substring(0, 20) + "..."
                            : row.nik}
                        </div>
                      </td>

                      {/* Wilayah */}
                      <td>
                        <div className="mb-cell-primary">{row.wilayah}</div>
                        <div className="mb-cell-secondary">{row.kecamatan}</div>
                      </td>

                      {/* Desil */}
                      <td style={{ textAlign: "center" }}>
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: getDesilColor(row.desil),
                            fontWeight: "600",
                            backgroundColor:
                              getDesilColor(row.desil) === "red"
                                ? "#fee2e2"
                                : getDesilColor(row.desil) === "orange"
                                  ? "#ffedd5"
                                  : "#dcfce7",
                            padding: "4px 12px",
                            borderRadius: "9999px",
                            fontSize: "13px",
                            minWidth: "70px",
                          }}
                        >
                          Desil {row.desil}
                        </span>
                      </td>

                      {/* ASPD Column */}
                      <td>
                        <div className="mb-cell-primary font-semibold text-blue-600">
                          {row.tahap === "analisis"
                            ? row.rekomendasiBantuan &&
                              row.rekomendasiBantuan.includes("ASPD")
                              ? `${row.skorASPD.toFixed(1)}`
                              : "—"
                            : row.bantuan && row.bantuan.includes("ASPD")
                              ? `${row.skorASPD.toFixed(1)}`
                              : "—"}
                        </div>
                      </td>

                      {/* PKHT Column */}
                      <td>
                        <div className="mb-cell-primary font-semibold text-purple-600">
                          {row.tahap === "analisis"
                            ? row.rekomendasiBantuan &&
                              row.rekomendasiBantuan.includes("PKHT")
                              ? `${row.skorPKHT.toFixed(1)}`
                              : "—"
                            : row.bantuan && row.bantuan.includes("PKHT")
                              ? `${row.skorPKHT.toFixed(1)}`
                              : "—"}
                        </div>
                      </td>

                      {/* Stage Badge (only on Semua tab) */}
                      {showStageBadge && (
                        <td>
                          <span
                            className={`mb-stage-badge ${getStageBadgeClass(row.tahap)}`}
                          >
                            <span className="mb-badge-dot" />
                            {getStageBadgeLabel(row.tahap)}
                          </span>
                        </td>
                      )}

                      {/* Bantuan */}
                      {showBantuan && (
                        <td style={{ fontWeight: 500 }}>
                          {row.bantuan && row.bantuan.length > 0 ? (
                            <div className="mb-bantuan-container">
                              {row.bantuan.slice(0, 2).join(", ")}
                              {row.bantuan.length > 2 && (
                                <span className="mb-bantuan-more">
                                  +{row.bantuan.length - 2} lainnya
                                </span>
                              )}
                              {row.bantuan.length > 2 && (
                                <div className="mb-bantuan-tooltip">
                                  {row.bantuan.join(", ")}
                                </div>
                              )}
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>
                      )}

                      {/* Desil Change (Evaluasi only) */}
                      {showDesilChange && (
                        <td>
                          {row.desilSebelum !== undefined &&
                          row.desilSesudah !== undefined ? (
                            <div className="mb-desil-change">
                              <span>Desil {row.desilSebelum}</span>
                              <ArrowRight
                                size={14}
                                className="mb-desil-arrow"
                              />
                              <span>Desil {row.desilSesudah}</span>
                              {row.desilSesudah > row.desilSebelum ? (
                                <span className="mb-desil-improved">
                                  ↑ Naik
                                </span>
                              ) : row.desilSesudah < row.desilSebelum ? (
                                <span className="mb-desil-declined">
                                  ↓ Turun
                                </span>
                              ) : (
                                <span className="mb-desil-unchanged">
                                  = Tetap
                                </span>
                              )}
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>
                      )}

                      {/* Actions */}
                      <td style={{ textAlign: "center" }}>
                        <div
                          className="mb-action-cell"
                          style={{
                            justifyContent: "center",
                            display: "flex",
                            gap: "8px",
                            alignItems: "center",
                          }}
                        >
                          {/* Proses-specific */}
                          {row.tahap === "proses" && (
                            <button
                              className="mb-btn-analisis"
                              style={{
                                width: "140px",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: "6px",
                                cursor: "not-allowed",
                                opacity: 0.8,
                              }}
                              disabled
                            >
                              <Loader2 size={14} className="mb-spin" /> Diproses...
                            </button>
                          )}

                          {/* Analisis-specific */}
                          {row.tahap === "analisis" && (
                            <button
                              className="mb-btn-analisis"
                              style={{
                                width: "140px",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: "6px",
                              }}
                              disabled={analyzingId === row.id_keluarga}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAnalisis(row.id_keluarga);
                              }}
                            >
                              {analyzingId === row.id_keluarga ? (
                                <>
                                  <Loader2 size={14} className="mb-spin" />{" "}
                                  Menganalisis...
                                </>
                              ) : (
                                <>
                                  <BrainCircuit size={14} /> Analisis
                                </>
                              )}
                            </button>
                          )}

                          {/* Validasi-specific */}
                          {row.tahap === "validasi" && (
                            <button
                              className="mb-btn-validasi"
                              style={{
                                width: "140px",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: "6px",
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detail-hasil/${row.id_keluarga}`, {
                                  state: row,
                                });
                              }}
                            >
                              <ShieldCheck size={14} /> Validasi
                            </button>
                          )}

                          {/* Diterima-specific */}
                          {row.tahap === "diterima" && (
                            <button
                              className="mb-btn-review"
                              style={{
                                width: "140px",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: "6px",
                                backgroundColor: "#ecfdf5",
                                color: "#10b981",
                                borderColor: "#a7f3d0",
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detail-hasil/${row.id_keluarga}`, {
                                  state: row,
                                });
                              }}
                            >
                              <CheckCircle size={14} /> Review Bantuan
                            </button>
                          )}

                          {/* Ditolak-specific */}
                          {row.tahap === "ditolak" && (
                            <button
                              className="mb-btn-history"
                              style={{
                                width: "140px",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: "6px",
                                backgroundColor: "#fef2f2",
                                color: "#ef4444",
                                borderColor: "#fecaca",
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detail-hasil/${row.id_keluarga}`, {
                                  state: row,
                                });
                              }}
                            >
                              <FileBarChart size={14} /> Lihat Detail
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Batch Action Bar */}
          {selectedRows.size > 0 && (
            <div className="mb-batch-bar">
              <div className="mb-batch-info">
                <CheckSquare size={18} style={{ color: "#2563eb" }} />
                <span>
                  <strong>{selectedRows.size}</strong> data terpilih
                </span>
                <button
                  className="mb-batch-clear"
                  onClick={() => setSelectedRows(new Set())}
                >
                  <XCircle size={14} /> Batal Pilih
                </button>
              </div>
              <button
                className="mb-batch-btn"
                onClick={handleBatchAnalisis}
                disabled={isBatchAnalyzing}
              >
                {isBatchAnalyzing ? (
                  <>
                    <Loader2 size={16} className="mb-spin" /> Menganalisis...{" "}
                    {batchProgress}%
                  </>
                ) : (
                  <>
                    <BrainCircuit size={16} /> Analisis Batch (
                    {selectedRows.size})
                  </>
                )}
              </button>
            </div>
          )}

          {/* Pagination */}
          {!isLoading && filteredData.length > 0 && (
            <div className="mb-pagination">
              <div className="mb-pagination-info">
                Menampilkan{" "}
                <strong>
                  {(currentPage - 1) * ITEMS_PER_PAGE + 1}–
                  {Math.min(currentPage * ITEMS_PER_PAGE, filteredData.length)}
                </strong>{" "}
                dari <strong>{filteredData.length}</strong> data
              </div>
              <div className="mb-pagination-controls">
                <button
                  className="mb-page-btn"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={16} />
                </button>
                {getPageNumbers().map((page, idx) =>
                  page === "..." ? (
                    <span
                      key={`ellipsis-${idx}`}
                      style={{
                        padding: "0 6px",
                        color: "#94a3b8",
                        fontSize: "13px",
                        userSelect: "none",
                      }}
                    >
                      …
                    </span>
                  ) : (
                    <button
                      key={page}
                      className={`mb-page-btn ${currentPage === page ? "active" : ""}`}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  ),
                )}
                <button
                  className="mb-page-btn"
                  disabled={currentPage === totalPages}
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
};

export default ManajemenBantuan;
