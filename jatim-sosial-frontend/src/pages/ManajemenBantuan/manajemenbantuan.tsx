import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "../../components/layout/AdminLayout";
import {
  Search,
  ChevronLeft,
  ChevronRight,
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
  skorPKHPlus?: number;

  // Variabel dinamis DTKS untuk kolom dan filter
  kelurahan_desa?: string;
  jumlah_anggota_keluarga?: number;
  luas_lantai_bangunan?: number;
  id_lantai_terluas?: number;
  id_dinding_terluas?: number;
  id_atap_terluas?: number;
  id_sumber_airminum?: number;
  id_sumberpenerangan?: number;
  id_bb_utama?: number;
  id_fasilitas_bab?: number;
  id_jenis_kloset?: number;
  id_pembuangan_tinja?: number;
  id_disabilitas?: number;
  tingkat_disabilitas?: string;
  pbi?: number;
  kpm_jawara?: number;
  putri_jawara?: number;
  aspd?: number;
  eks_ppks_jawara?: number;
  ppks_jawara?: number;
  kemiskinan_ekstrem?: number;
  pkh_plus?: number;
  aset_bergerak_tabung_gas?: number;
  aset_bergerak_lemari_es?: number;
  aset_bergerak_ac?: number;
  aset_bergerak_pemanas_air?: number;
  aset_bergerak_telepon_rumah?: number;
  aset_bergerak_tv_datar?: number;
  aset_bergerak_emas_perhiasan?: number;
  aset_bergerak_komputer_laptop_tablet?: number;
  aset_bergerak_sepeda_motor?: number;
  aset_bergerak_sepeda?: number;
  aset_bergerak_mobil?: number;
  aset_bergerak_perahu?: number;
  aset_bergerak_kapal_perahu_motor?: number;
  aset_bergerak_smartphone?: number;
}

interface ColumnConfig {
  key: string;
  label: string;
  locked?: boolean;
  defaultVisible?: boolean;
}

const COLUMNS: ColumnConfig[] = [
  { key: "id_keluarga", label: "ID / Tanggal", defaultVisible: true },
  { key: "nama", label: "Nama Penerima", locked: true, defaultVisible: true },
  { key: "nik", label: "NIK", defaultVisible: true },
  { key: "wilayah", label: "Wilayah / Kota", defaultVisible: true },
  { key: "kecamatan", label: "Kecamatan", defaultVisible: true },
  { key: "kelurahan_desa", label: "Kelurahan / Desa", defaultVisible: false },
  { key: "desil", label: "Desil Ekonomi", defaultVisible: true },
  { key: "skor_aspd", label: "Skor ASPD", defaultVisible: true },
  { key: "skor_pkh_plus", label: "Skor PKHT", defaultVisible: true },
  { key: "tahap", label: "Status Tahap", defaultVisible: true },
  { key: "bantuan", label: "Bantuan", locked: true, defaultVisible: true },
  
  // DTKS Extra fields
  { key: "jumlah_anggota_keluarga", label: "Jml Anggota Keluarga", defaultVisible: false },
  { key: "luas_lantai_bangunan", label: "Luas Lantai (m²)", defaultVisible: false },
  { key: "id_lantai_terluas", label: "ID Lantai Terluas", defaultVisible: false },
  { key: "id_dinding_terluas", label: "ID Dinding Terluas", defaultVisible: false },
  { key: "id_atap_terluas", label: "ID Atap Terluas", defaultVisible: false },
  { key: "id_sumber_airminum", label: "ID Sumber Air", defaultVisible: false },
  { key: "id_sumberpenerangan", label: "ID Penerangan", defaultVisible: false },
  { key: "id_bb_utama", label: "ID BB Utama", defaultVisible: false },
  { key: "id_fasilitas_bab", label: "ID Fasilitas BAB", defaultVisible: false },
  { key: "id_jenis_kloset", label: "ID Jenis Kloset", defaultVisible: false },
  { key: "id_pembuangan_tinja", label: "ID Pembuangan Tinja", defaultVisible: false },
  { key: "id_disabilitas", label: "ID Disabilitas", defaultVisible: false },
  { key: "tingkat_disabilitas", label: "Tingkat Disabilitas", defaultVisible: false },
  { key: "pbi", label: "PBI", defaultVisible: false },
  { key: "kpm_jawara", label: "KPM Jawara", defaultVisible: false },
  { key: "putri_jawara", label: "Putri Jawara", defaultVisible: false },
  { key: "aspd", label: "ASPD Flag", defaultVisible: false },
  { key: "eks_ppks_jawara", label: "Eks PPKS Jawara", defaultVisible: false },
  { key: "ppks_jawara", label: "PPKS Jawara", defaultVisible: false },
  { key: "kemiskinan_ekstrem", label: "Kemiskinan Ekstrem", defaultVisible: false },
  { key: "pkh_plus", label: "PKH Plus Flag", defaultVisible: false },
  
  // Aset Extra fields
  { key: "aset_bergerak_tabung_gas", label: "Aset: Tabung Gas", defaultVisible: false },
  { key: "aset_bergerak_lemari_es", label: "Aset: Lemari Es", defaultVisible: false },
  { key: "aset_bergerak_ac", label: "Aset: AC", defaultVisible: false },
  { key: "aset_bergerak_pemanas_air", label: "Aset: Pemanas Air", defaultVisible: false },
  { key: "aset_bergerak_telepon_rumah", label: "Aset: Telp Rumah", defaultVisible: false },
  { key: "aset_bergerak_tv_datar", label: "Aset: TV Datar", defaultVisible: false },
  { key: "aset_bergerak_emas_perhiasan", label: "Aset: Emas Perhiasan", defaultVisible: false },
  { key: "aset_bergerak_komputer_laptop_tablet", label: "Aset: Laptop/Tablet", defaultVisible: false },
  { key: "aset_bergerak_sepeda_motor", label: "Aset: Sepeda Motor", defaultVisible: false },
  { key: "aset_bergerak_sepeda", label: "Aset: Sepeda", defaultVisible: false },
  { key: "aset_bergerak_mobil", label: "Aset: Mobil", defaultVisible: false },
  { key: "aset_bergerak_perahu", label: "Aset: Perahu", defaultVisible: false },
  { key: "aset_bergerak_kapal_perahu_motor", label: "Aset: Kapal Motor", defaultVisible: false },
  { key: "aset_bergerak_smartphone", label: "Aset: Smartphone", defaultVisible: false },

  { key: "aksi", label: "Aksi", locked: true, defaultVisible: true }
];

interface ManajemenBantuanProps {
  onLogout?: () => void;
}

type TabKey = "semua" | Tahap;
type SortKey = string;

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

const isNumericColumn = (key: string): boolean => {
  const numericPrefixes = ["id_", "aset_", "skor", "desil", "pbi", "kpm_", "putri_", "aspd", "pkh_plus", "kemiskinan_", "luas_", "jumlah_"];
  return numericPrefixes.some(prefix => key.toLowerCase().startsWith(prefix)) || ["skorASPD", "skorPKHT", "desil"].includes(key);
};

/* ─── Component ──────────────────────────── */

const ManajemenBantuan: React.FC<ManajemenBantuanProps> = ({ onLogout }) => {
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState<TabKey>("semua");
  const [searchTerm, setSearchTerm] = useState("");

  // New filters states
  const [filterKecamatan, setFilterKecamatan] = useState("Semua");
  const [filterKelurahan, setFilterKelurahan] = useState("Semua");
  const [selectedDesils, setSelectedDesils] = useState<number[]>([]);
  const [filterOverlap, setFilterOverlap] = useState("Semua");

  // Popovers state
  const [showColumnDropdown, setShowColumnDropdown] = useState(false);
  const [showDesilDropdown, setShowDesilDropdown] = useState(false);

  // Column visibility state loaded from localStorage
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(() => {
    const saved = localStorage.getItem("mb-visible-columns");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return new Set(parsed);
        }
      } catch (e) {
        console.error(e);
      }
    }
    return new Set(COLUMNS.filter(c => c.defaultVisible || c.locked).map(c => c.key));
  });

  // Save visible columns
  useEffect(() => {
    localStorage.setItem("mb-visible-columns", JSON.stringify(Array.from(visibleColumns)));
  }, [visibleColumns]);

  // Click outside to close dropdowns
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".mb-popover-wrapper")) {
        setShowColumnDropdown(false);
        setShowDesilDropdown(false);
      }
    };
    document.addEventListener("click", handleOutsideClick);
    return () => document.removeEventListener("click", handleOutsideClick);
  }, []);

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
  const latestRequestRef = React.useRef(0);

  const fetchData = useCallback(async (showLoading = false) => {
    const requestId = ++latestRequestRef.current;
    try {
      if (showLoading) setIsLoading(true);
      const res = await apiFetch("/api/v1/manajemen-bantuan");
      if (res.ok && requestId === latestRequestRef.current) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      if (requestId === latestRequestRef.current) {
        console.error("Gagal mengambil data dari server:", e);
      }
    } finally {
      if (showLoading && requestId === latestRequestRef.current) {
        setIsLoading(false);
      }
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
  }, [activeTab, searchTerm, filterKecamatan, filterKelurahan, filterOverlap, selectedDesils]);

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

    // Advanced Wilayah: Kecamatan & Kelurahan
    if (filterKecamatan !== "Semua") {
      result = result.filter((d) => d.kecamatan === filterKecamatan);
    }
    if (filterKelurahan !== "Semua") {
      result = result.filter((d) => d.kelurahan_desa === filterKelurahan || (d as any).kelurahan === filterKelurahan);
    }



    // Advanced Assistance Intersection / Overlap
    if (filterOverlap !== "Semua") {
      result = result.filter((d) => {
        const list = d.bantuan || [];
        const hasPKHT = list.includes("PKHT");
        const hasASPD = list.includes("ASPD");

        if (filterOverlap === "HanyaPKHT") return hasPKHT && !hasASPD;
        if (filterOverlap === "HanyaASPD") return hasASPD && !hasPKHT;
        if (filterOverlap === "Keduanya") return hasPKHT && hasASPD;
        if (filterOverlap === "BelumMenerima") return !hasPKHT && !hasASPD;
        return true;
      });
    }

    // Advanced Desil Multi-select
    if (selectedDesils.length > 0) {
      result = result.filter((d) => selectedDesils.includes(d.desil));
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

        if (sortConfig.key === "id_keluarga") {
          valA = a.idLabel;
          valB = b.idLabel;
        } else if (sortConfig.key === "bantuan") {
          valA = a.bantuan ? a.bantuan.join(", ") : "";
          valB = b.bantuan ? b.bantuan.join(", ") : "";
        } else if (sortConfig.key === "tahap") {
          valA = tahapOrder[a.tahap] || 99;
          valB = tahapOrder[b.tahap] || 99;
        } else if (sortConfig.key === "skor_aspd") {
          valA = a.skorASPD ?? 0;
          valB = b.skorASPD ?? 0;
        } else if (sortConfig.key === "skor_pkh_plus") {
          valA = a.skorPKHPlus ?? a.skorPKHT ?? 0;
          valB = b.skorPKHPlus ?? b.skorPKHT ?? 0;
        }

        const isNum = isNumericColumn(sortConfig.key);
        if (valA === undefined || valA === null) valA = isNum ? 0 : "";
        if (valB === undefined || valB === null) valB = isNum ? 0 : "";

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
    filterKecamatan,
    filterKelurahan,
    filterOverlap,
    selectedDesils,
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

  // Dynamic lists for filters
  const kecamatanList = useMemo(() => {
    const set = new Set<string>();
    data.forEach((d) => {
      if (d.kecamatan) set.add(d.kecamatan);
    });
    return Array.from(set).sort();
  }, [data]);

  const kelurahanList = useMemo(() => {
    const set = new Set<string>();
    data.forEach((d) => {
      if (filterKecamatan === "Semua" || d.kecamatan === filterKecamatan) {
        if (d.kelurahan_desa) set.add(d.kelurahan_desa);
        else if ((d as any).kelurahan) set.add((d as any).kelurahan);
      }
    });
    return Array.from(set).sort();
  }, [data, filterKecamatan]);

  const resetFilters = () => {
    setSearchTerm("");
    setFilterKecamatan("Semua");
    setFilterKelurahan("Semua");
    setSelectedDesils([]);
    setFilterOverlap("Semua");
    setSortConfig(null);
  };

  const resetColumns = () => {
    setVisibleColumns(new Set(COLUMNS.filter(c => c.defaultVisible || c.locked).map(c => c.key)));
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
    const isNum = isNumericColumn(sortKey);

    let sortBadgeText = "";
    if (isActive) {
      if (isNum) {
        sortBadgeText = sortConfig.direction === "asc" ? "Terkecil - Terbesar" : "Terbesar - Terkecil";
      } else {
        sortBadgeText = sortConfig.direction === "asc" ? "A-Z" : "Z-A";
      }
    }

    return (
      <th
        className="mb-th-sortable"
        onClick={() => handleSort(sortKey)}
        title={`Klik untuk mengurutkan berdasarkan ${label.toLowerCase()}`}
        style={{
          cursor: "pointer",
          padding: "14px 16px",
          color: isActive ? "#2563eb" : "#475569",
          backgroundColor: isActive ? "#f8fafc" : "transparent",
          transition: "all 0.2s ease"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "nowrap" }}>
          <span style={{ fontSize: "12px", fontWeight: "600", textTransform: "uppercase" }}>{label}</span>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <span className={`mb-sort-icon ${isActive ? "active" : ""}`} style={{ color: isActive ? "#2563eb" : "#cbd5e1" }}>
              {isActive && sortConfig.direction === "asc" ? (
                <ChevronUp size={14} />
              ) : isActive && sortConfig.direction === "desc" ? (
                <ChevronDown size={14} />
              ) : (
                <ChevronsUpDown size={14} />
              )}
            </span>
            {isActive && sortBadgeText && (
              <span
                style={{
                  fontSize: "9px",
                  fontWeight: 600,
                  backgroundColor: "#eff6ff",
                  color: "#2563eb",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  border: "1px solid #bfdbfe",
                  whiteSpace: "nowrap",
                  textTransform: "none"
                }}
              >
                {sortBadgeText}
              </span>
            )}
          </div>
        </div>
      </th>
    );
  };

  const colCount =
    1 + // checkbox
    COLUMNS.filter((c) => visibleColumns.has(c.key) || c.locked).length;

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
        <div className="mb-filter-bar" style={{ display: "flex", flexDirection: "column", gap: "16px", padding: "20px" }}>
          <div style={{ display: "flex", width: "100%", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
            <div className="mb-search-box" style={{ flex: 1, minWidth: "280px" }}>
              <Search size={18} />
              <input
                type="text"
                placeholder="Cari Nama / NIK / ID Analisis..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                disabled={isLoading}
              />
            </div>

            {/* Kolom Manager Popover */}
            <div className="mb-popover-wrapper" style={{ position: "relative" }}>
              <button
                className="mb-btn-reset"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowColumnDropdown(!showColumnDropdown);
                  setShowDesilDropdown(false);
                }}
                style={{ height: "42px", display: "flex", alignItems: "center" }}
              >
                Atur Kolom
              </button>
              {showColumnDropdown && (
                <div className="mb-popover-menu" onClick={(e) => e.stopPropagation()} style={{ position: "absolute", zIndex: 100, right: 0, marginTop: "8px" }}>
                  <div className="mb-popover-header">Visibilitas Kolom</div>
                  <div className="mb-popover-list" style={{ maxHeight: "300px", overflowY: "auto" }}>
                    {COLUMNS.map((col) => {
                      const isLocked = col.locked;
                      const isChecked = visibleColumns.has(col.key) || isLocked;
                      return (
                        <label key={col.key} className="mb-popover-item" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 12px", cursor: "pointer" }}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            disabled={isLocked}
                            onChange={() => {
                              setVisibleColumns((prev) => {
                                const next = new Set(prev);
                                if (next.has(col.key)) {
                                  next.delete(col.key);
                                } else {
                                  next.add(col.key);
                                }
                                return next;
                              });
                            }}
                          />
                          <span className={isLocked ? "mb-column-locked" : ""} style={{ fontSize: "14px", color: isLocked ? "#94a3b8" : "#334155" }}>
                            {col.label} {isLocked && "(Wajib)"}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>





            <button
              className="mb-btn-reset"
              onClick={resetColumns}
              disabled={isLoading}
              style={{ height: "42px", display: "flex", alignItems: "center" }}
            >
              Reset Kolom
            </button>
          </div>

          {/* Baris Kedua: Advanced Filters */}
          <div style={{ display: "flex", width: "100%", gap: "16px", flexWrap: "wrap", alignItems: "center", borderTop: "1px solid #f1f5f9", paddingTop: "16px" }}>
            <div className="mb-filter-group" style={{ minWidth: "160px" }}>
              <label>KECAMATAN</label>
              <select
                value={filterKecamatan}
                onChange={(e) => {
                  setFilterKecamatan(e.target.value);
                  setFilterKelurahan("Semua");
                }}
                disabled={isLoading}
              >
                <option value="Semua">Semua Kecamatan</option>
                {kecamatanList.map((kec) => (
                  <option key={kec} value={kec}>{kec}</option>
                ))}
              </select>
            </div>

            <div className="mb-filter-group" style={{ minWidth: "160px" }}>
              <label>KELURAHAN / DESA</label>
              <select
                value={filterKelurahan}
                onChange={(e) => setFilterKelurahan(e.target.value)}
                disabled={isLoading || filterKecamatan === "Semua"}
              >
                <option value="Semua">Semua Kelurahan/Desa</option>
                {kelurahanList.map((kel) => (
                  <option key={kel} value={kel}>{kel}</option>
                ))}
              </select>
            </div>



            <div className="mb-filter-group" style={{ minWidth: "180px" }}>
              <label>INTERSEKSI BANTUAN</label>
              <select
                value={filterOverlap}
                onChange={(e) => setFilterOverlap(e.target.value)}
                disabled={isLoading}
              >
                <option value="Semua">Semua Penerima</option>
                <option value="HanyaPKHT">Hanya PKHT</option>
                <option value="HanyaASPD">Hanya ASPD</option>
                <option value="Keduanya">Menerima Keduanya (Overlap)</option>
                <option value="BelumMenerima">Belum Menerima PKHT/ASPD</option>
              </select>
            </div>

            {/* Desil Multi-Select Dropdown */}
            <div className="mb-filter-group mb-popover-wrapper" style={{ position: "relative", minWidth: "160px" }}>
              <label>DESIL EKONOMI</label>
              <button
                className="mb-multiselect-box"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDesilDropdown(!showDesilDropdown);
                  setShowColumnDropdown(false);
                }}
                style={{ width: "100%", textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center", height: "42px" }}
              >
                <span>
                  {selectedDesils.length === 0
                    ? "Semua Desil"
                    : `Desil: ${selectedDesils.sort((a,b)=>a-b).join(", ")}`}
                </span>
                <ChevronDown size={14} />
              </button>
              {showDesilDropdown && (
                <div className="mb-popover-menu" onClick={(e) => e.stopPropagation()} style={{ position: "absolute", zIndex: 100, left: 0, marginTop: "8px", width: "180px" }}>
                  <div className="mb-popover-header">Pilih Desil</div>
                  <div className="mb-popover-list" style={{ maxHeight: "200px", overflowY: "auto" }}>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((desil) => {
                      const isChecked = selectedDesils.includes(desil);
                      return (
                        <label key={desil} className="mb-popover-item" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 12px", cursor: "pointer" }}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {
                              setSelectedDesils((prev) => {
                                if (prev.includes(desil)) {
                                  return prev.filter((d) => d !== desil);
                                } else {
                                  return [...prev, desil];
                                }
                              });
                            }}
                          />
                          <span>Desil {desil}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <button
              className="mb-btn-reset"
              onClick={resetFilters}
              disabled={isLoading}
              style={{ height: "42px", display: "flex", alignItems: "center" }}
            >
              Reset Filter
            </button>
          </div>
        </div>

        {/* ── Data Table ────────────────────── */}
        <div className="mb-table-card">
          <div className="mb-table-responsive" style={{ overflowX: "auto" }}>
            <table className="mb-table" style={{ tableLayout: "auto", width: "100%" }}>
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
                  {COLUMNS.map((col) => {
                    if (!visibleColumns.has(col.key) && !col.locked) return null;
                    if (col.key === "aksi") {
                      return <th key={col.key} style={{ padding: "14px 16px", color: "#475569", fontSize: "12px", fontWeight: "600", textTransform: "uppercase", textAlign: "center" }}>{col.label}</th>;
                    }
                    return renderSortHeader(col.label.toUpperCase(), col.key);
                  })}
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

                      {/* Dynamic Columns Cell Mapping */}
                      {COLUMNS.map((col) => {
                        if (!visibleColumns.has(col.key) && !col.locked) return null;

                        switch (col.key) {
                          case "id_keluarga":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
                                <div className="mb-id-col" style={{ display: "flex", flexDirection: "column" }}>
                                  <span className="mb-cell-link" style={{ fontWeight: 600 }}>{row.idLabel}</span>
                                  <span style={{ fontSize: "11px", color: "#64748b" }}>{row.tanggal || "-"}</span>
                                </div>
                              </td>
                            );
                          case "nama":
                            const isNikColumnVisible = visibleColumns.has("nik");
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
                                <div style={{ display: "flex", flexDirection: "column" }}>
                                  <span style={{ fontWeight: 600, color: "#1e293b" }}>{row.nama}</span>
                                  {!isNikColumnVisible && (
                                    <>
                                      <span style={{ fontSize: "12px", color: "#64748b" }}>
                                        NIK: {row.nik.length > 20 ? row.nik.substring(0, 20) + "..." : row.nik}
                                      </span>
                                      {row.nik && (row.nik.includes("0000") || row.nik.length < 16) && (
                                        <span style={{ fontSize: "10px", color: "#ef4444", background: "#fef2f2", padding: "2px 6px", borderRadius: "4px", width: "fit-content", marginTop: "4px", fontWeight: 600 }}>
                                          Anomali NIK
                                        </span>
                                      )}
                                    </>
                                  )}
                                </div>
                              </td>
                            );
                          case "wilayah":
                            const isKecamatanVisible = visibleColumns.has("kecamatan");
                            const isKelurahanVisible = visibleColumns.has("kelurahan_desa");
                            const showWilayahSubtext = !isKecamatanVisible && !isKelurahanVisible;
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
                                <div style={{ display: "flex", flexDirection: "column" }}>
                                  <span style={{ fontWeight: 500, color: "#334155" }}>{row.wilayah}</span>
                                  {showWilayahSubtext && (
                                    <span style={{ fontSize: "12px", color: "#64748b" }}>
                                      {row.kecamatan || "-"}, {row.kelurahan_desa || "-"}
                                    </span>
                                  )}
                                </div>
                              </td>
                            );
                          case "desil":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
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
                            );
                          case "skor_aspd":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px", fontWeight: 600, color: "#2563eb" }}>
                                {(row.skorASPD ?? 0).toFixed(1)}
                              </td>
                            );
                          case "skor_pkh_plus":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px", fontWeight: 600, color: "#7c3aed" }}>
                                {(row.skorPKHPlus ?? row.skorPKHT ?? 0).toFixed(1)}
                              </td>
                            );
                          case "tahap":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
                                <span className={`mb-stage-badge ${getStageBadgeClass(row.tahap)}`} style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                                  <span className="mb-badge-dot" />
                                  {getStageBadgeLabel(row.tahap)}
                                </span>
                              </td>
                            );
                          case "bantuan":
                            return (
                              <td key={col.key} style={{ padding: "14px 16px" }}>
                                {row.bantuan && row.bantuan.length > 0 ? (
                                  <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                                    {row.bantuan.map((b) => (
                                      <span key={b} className={`mb-pill-bantuan ${b.toLowerCase()}`} style={{ fontSize: "11px", fontWeight: "600", padding: "2px 8px", borderRadius: "4px", backgroundColor: b === "ASPD" ? "#eff6ff" : "#f5f3ff", color: b === "ASPD" ? "#1d4ed8" : "#6d28d9", border: `1px solid ${b === "ASPD" ? "#bfdbfe" : "#ddd6fe"}` }}>
                                        {b}
                                      </span>
                                    ))}
                                  </div>
                                ) : (
                                  <span style={{ color: "#94a3b8", fontSize: "13px" }}>—</span>
                                )}
                              </td>
                            );
                          case "aksi":
                            return (
                              <td key={col.key} onClick={(e) => e.stopPropagation()} style={{ padding: "14px 16px", textAlign: "center" }}>
                                <div style={{ display: "flex", justifyContent: "center", gap: "8px", alignItems: "center" }}>
                                  {row.tahap === "proses" && (
                                    <button
                                      className="mb-btn-analisis"
                                      style={{
                                        width: "120px",
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

                                  {row.tahap === "analisis" && (
                                    <button
                                      className="mb-btn-analisis"
                                      style={{
                                        width: "120px",
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
                                          <Loader2 size={14} className="mb-spin" /> Menganalisis
                                        </>
                                      ) : (
                                        <>
                                          <BrainCircuit size={14} /> Analisis
                                        </>
                                      )}
                                    </button>
                                  )}

                                  {row.tahap === "validasi" && (
                                    <button
                                      className="mb-btn-validasi"
                                      style={{
                                        width: "120px",
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

                                  {(row.tahap === "diterima" || row.tahap === "ditolak") && (
                                    <button
                                      className="mb-btn-review"
                                      style={{
                                        width: "120px",
                                        display: "inline-flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        gap: "6px",
                                        backgroundColor: row.tahap === "diterima" ? "#ecfdf5" : "#fef2f2",
                                        color: row.tahap === "diterima" ? "#10b981" : "#ef4444",
                                        borderColor: row.tahap === "diterima" ? "#a7f3d0" : "#fecaca",
                                      }}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/detail-hasil/${row.id_keluarga}`, {
                                          state: row,
                                        });
                                      }}
                                    >
                                      {row.tahap === "diterima" ? <CheckCircle size={14} /> : <FileBarChart size={14} />} Review
                                    </button>
                                  )}
                                </div>
                              </td>
                            );
                          default:
                            const val = row[col.key as keyof DataRow];
                            let displayVal = "—";
                            if (typeof val === "boolean") {
                              displayVal = val ? "Ya" : "Tidak";
                            } else if (typeof val === "number") {
                              displayVal = val.toLocaleString();
                            } else if (val) {
                              displayVal = String(val);
                            }
                            return (
                              <td key={col.key} style={{ padding: "14px 16px", color: "#475569", fontSize: "13px" }}>
                                {displayVal}
                              </td>
                            );
                        }
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Batch Action Bar */}
          {selectedRows.size > 0 && (
            <div className="mb-batch-bar" style={{ display: "flex", justifyContent: "space-between", padding: "16px 20px", backgroundColor: "#f8fafc", borderTop: "1px solid #e2e8f0" }}>
              <div className="mb-batch-info" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <CheckSquare size={18} style={{ color: "#2563eb" }} />
                <span>
                  <strong>{selectedRows.size}</strong> data keluarga terpilih
                </span>
                <button
                  className="mb-batch-clear"
                  onClick={() => setSelectedRows(new Set())}
                  style={{ display: "flex", alignItems: "center", gap: "4px", color: "#64748b", background: "none", border: "none", cursor: "pointer", fontSize: "13px" }}
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
                    <Loader2 size={16} className="mb-spin" /> Menganalisis... {batchProgress}%
                  </>
                ) : (
                  <>
                    <BrainCircuit size={16} /> Analisis Batch ({selectedRows.size})
                  </>
                )}
              </button>
            </div>
          )}

          {/* Pagination */}
          {!isLoading && filteredData.length > 0 && (
            <div className="mb-pagination" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", borderTop: "1px solid #e2e8f0" }}>
              <div className="mb-pagination-info" style={{ fontSize: "14px", color: "#64748b" }}>
                Menampilkan{" "}
                <strong>
                  {(currentPage - 1) * ITEMS_PER_PAGE + 1}–
                  {Math.min(currentPage * ITEMS_PER_PAGE, filteredData.length)}
                </strong>{" "}
                dari <strong>{filteredData.length}</strong> data keluarga
              </div>
              <div className="mb-pagination-controls" style={{ display: "flex", gap: "6px" }}>
                <button
                  className="mb-page-btn"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
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
                        alignSelf: "center",
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
                  )
                )}
                <button
                  className="mb-page-btn"
                  disabled={currentPage === totalPages}
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
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
