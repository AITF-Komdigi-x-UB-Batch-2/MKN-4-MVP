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
  Loader2,
  ShieldCheck,
  BrainCircuit,
  CheckSquare,
  Square,
  XCircle,
  Filter,
} from "lucide-react";
import LoadingState from "../../components/ui/LoadingState";
import EmptyState from "../../components/ui/EmptyState";
import type { Tahap, AnalisisOutput } from "../../data/mockData";
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
  skorPKHPlus: number;
  skorPKHT?: number;

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

interface PaginatedManajemenBantuanResponse {
  data: DataRow[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    counts: Record<string, number>;
  };
}

const COLUMNS: ColumnConfig[] = [
  { key: "id_keluarga", label: "ID / Tanggal", defaultVisible: true },
  { key: "nama", label: "Nama Penerima", locked: true, defaultVisible: true },
  { key: "nik", label: "NIK", defaultVisible: true },
  { key: "wilayah", label: "Wilayah / Kota", defaultVisible: true },
  { key: "kecamatan", label: "Kecamatan", defaultVisible: true },
  { key: "kelurahan_desa", label: "Kelurahan / Desa", defaultVisible: false },
  { key: "desil", label: "Desil Ekonomi", defaultVisible: true },

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

  // Indikator Kemiskinan Ekstrem
  { key: "skor_aspd", label: "Skor ASPD", defaultVisible: true },
  { key: "skor_pkh_plus", label: "Skor PKH+", defaultVisible: true },
  { key: "tahap", label: "Status Tahap", defaultVisible: true },
  { key: "bantuan", label: "Bantuan Eligible", locked: true, defaultVisible: true },
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
  return numericPrefixes.some(prefix => key.toLowerCase().startsWith(prefix)) || ["skorASPD", "skorPKHPlus", "desil"].includes(key);
};

const getColValue = (row: DataRow, key: string): string => {
  switch (key) {
    case 'id_keluarga': return row.idLabel;
    case 'tahap': return getStageBadgeLabel(row.tahap);
    case 'bantuan': return (row.bantuan || []).join(', ') || '—';
    case 'skor_aspd': return String((row.skorASPD ?? 0).toFixed(1));
    case 'skor_pkh_plus': return String((row.skorPKHPlus ?? row.skorPKHT ?? 0).toFixed(1));
    case 'desil': return String(row.desil ?? '—');
    default: { const v = row[key as keyof DataRow]; return v !== undefined && v !== null ? String(v) : '—'; }
  }
};

// Kolom yang nilai uniknya sangat banyak (tidak boleh pakai checkbox — akan crash browser)
// Gunakan text search sebagai gantinya
const HIGH_CARDINALITY_COLS = new Set(['id_keluarga', 'nama', 'nik']);

// Batas maksimal unique values yang ditampilkan sebagai checkbox
const MAX_CHECKBOX_VALUES = 300;

/* ─── Component ──────────────────────────── */

const ManajemenBantuan: React.FC<ManajemenBantuanProps> = ({ onLogout }) => {
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState<TabKey>("semua");
  const [searchTerm, setSearchTerm] = useState("");
  const [searchColumn, setSearchColumn] = useState("");

  // New filters states
  const [filterKecamatan, setFilterKecamatan] = useState("Semua");
  const [filterKelurahan, setFilterKelurahan] = useState("Semua");
  const [selectedDesils, setSelectedDesils] = useState<number[]>([]);
  const [filterOverlap, setFilterOverlap] = useState("Semua");

  // Popovers state
  const [showColumnDropdown, setShowColumnDropdown] = useState(false);
  const [, setShowDesilDropdown] = useState(false);
  const [openFilterCol, setOpenFilterCol] = useState<string | null>(null);
  const [columnFilters, setColumnFilters] = useState<Record<string, Set<string>>>({});
  const [textColumnFilters, setTextColumnFilters] = useState<Record<string, string>>({});
  const [pendingFilter, setPendingFilter] = useState<Set<string>>(new Set());
  const [pendingTextFilter, setPendingTextFilter] = useState('');
  const [filterDropdownSearch, setFilterDropdownSearch] = useState('');

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
      if (!target.closest(".excel-filter-th")) {
        setOpenFilterCol(null);
      }
    };
    document.addEventListener("click", handleOutsideClick);
    return () => document.removeEventListener("click", handleOutsideClick);
  }, []);

  useEffect(() => {
    if (!showColumnDropdown) {
      setSearchColumn("");
    }
  }, [showColumnDropdown]);

  const [sortConfig, setSortConfig] = useState<{
    key: SortKey;
    direction: "asc" | "desc";
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [data, setData] = useState<DataRow[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;
  const [serverTotalItems, setServerTotalItems] = useState(0);
  const [serverTotalPages, setServerTotalPages] = useState(1);
  const [serverTabCounts, setServerTabCounts] = useState<Record<TabKey, number>>({
    semua: 0,
    proses: 0,
    analisis: 0,
    validasi: 0,
    diterima: 0,
    ditolak: 0,
  });

  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const latestRequestRef = React.useRef(0);

  const displayData = useMemo(() => {
    return data.map((row) =>
      processingIds.has(row.id_keluarga)
        ? { ...row, tahap: "proses" as Tahap }
        : row,
    );
  }, [data, processingIds]);

  const fetchData = useCallback(async (showLoading = false) => {
    const requestId = ++latestRequestRef.current;
    console.log(`[fetchData] Memulai pengambilan data. Request ID: ${requestId}, Tab: "${activeTab}", Halaman: ${currentPage}, Pencarian: "${searchTerm}"`);
    try {
      if (showLoading) setIsLoading(true);
      const params = new URLSearchParams({
        page: String(currentPage),
        limit: String(ITEMS_PER_PAGE),
      });
      if (activeTab !== "semua") params.set("tahap", activeTab);
      if (searchTerm.trim()) params.set("search", searchTerm.trim());
      if (filterKecamatan !== "Semua") params.set("kecamatan", filterKecamatan);
      if (filterKelurahan !== "Semua") params.set("kelurahan_desa", filterKelurahan);
      if (filterOverlap !== "Semua") params.set("overlap", filterOverlap);
      if (selectedDesils.length > 0) params.set("desils", selectedDesils.join(","));

      const res = await apiFetch(`/api/v1/manajemen-bantuan?${params.toString()}`);
      if (res.ok && requestId === latestRequestRef.current) {
        const json = (await res.json()) as PaginatedManajemenBantuanResponse | DataRow[];
        console.log(`[fetchData] Berhasil mengambil data. Request ID: ${requestId}.`, json);
        if (Array.isArray(json)) {
          setData(json);
          setServerTotalItems(json.length);
          setServerTotalPages(Math.max(1, Math.ceil(json.length / ITEMS_PER_PAGE)));
        } else {
          setData(json.data);
          setServerTotalItems(json.meta.total);
          setServerTotalPages(json.meta.totalPages);
          setServerTabCounts({
            semua: json.meta.counts.semua || 0,
            proses: json.meta.counts.proses || 0,
            analisis: json.meta.counts.analisis || 0,
            validasi: json.meta.counts.validasi || 0,
            diterima: json.meta.counts.diterima || 0,
            ditolak: json.meta.counts.ditolak || 0,
          });
        }
      }
    } catch (e) {
      if (requestId === latestRequestRef.current) {
        console.error(`[fetchData] Gagal mengambil data. Request ID: ${requestId}. Error:`, e);
      }
    } finally {
      if (showLoading && requestId === latestRequestRef.current) {
        setIsLoading(false);
      }
    }
  }, [
    activeTab,
    currentPage,
    filterKecamatan,
    filterKelurahan,
    filterOverlap,
    searchTerm,
    selectedDesils,
  ]);

  useEffect(() => {
    if (currentPage > serverTotalPages) {
      setCurrentPage(serverTotalPages);
    }
  }, [currentPage, serverTotalPages]);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const hasProcessingData = displayData.some((row) => row.tahap === "proses");
    setIsMonitoring(hasProcessingData);

    if (!hasProcessingData) return;

    const pollInterval = setInterval(() => {
      fetchData();
    }, 4000);

    return () => clearInterval(pollInterval);
  }, [displayData, fetchData]);

  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, searchTerm, filterKecamatan, filterKelurahan, filterOverlap, selectedDesils]);

  // Counts per tab (before search/filter)
  const tabCounts = useMemo(() => {
    const counts = { ...serverTabCounts };
    let prosesTambahan = 0;
    let analisisBerkurang = 0;

    processingIds.forEach((id) => {
      const row = data.find((item) => item.id_keluarga === id);
      if (!row) return;
      if (row.tahap === "analisis") {
        analisisBerkurang += 1;
        prosesTambahan += 1;
      }
    });

    counts.analisis = Math.max(0, (counts.analisis || 0) - analisisBerkurang);
    counts.proses = (counts.proses || 0) + prosesTambahan;
    counts.semua = Math.max(0, (counts.semua || 0) - analisisBerkurang + prosesTambahan);
    return counts;
  }, [data, processingIds, serverTabCounts]);

  // Filtered data
  const filteredData = useMemo(() => {
    let result = displayData;

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
      result = result.filter((d) => d.kelurahan_desa === filterKelurahan || (d as DataRow & { kelurahan?: string }).kelurahan === filterKelurahan);
    }



    // Advanced Assistance Intersection / Overlap
    if (filterOverlap !== "Semua") {
      result = result.filter((d) => {
        const list = d.bantuan || [];
        const hasPKHPlus = list.includes("PKH+") || list.includes("PKH Plus") || list.includes("PKHT");
        const hasASPD = list.includes("ASPD");

        if (filterOverlap === "HanyaPKHPlus") return hasPKHPlus && !hasASPD;
        if (filterOverlap === "HanyaASPD") return hasASPD && !hasPKHPlus;
        if (filterOverlap === "Keduanya") return hasPKHPlus && hasASPD;
        if (filterOverlap === "BelumMenerima") return !hasPKHPlus && !hasASPD;
        return true;
      });
    }

    // Advanced Desil Multi-select
    if (selectedDesils.length > 0) {
      result = result.filter((d) => selectedDesils.includes(d.desil));
    }

    // Column value filters — checkbox (categorical)
    Object.entries(columnFilters).forEach(([key, allowed]) => {
      if (allowed.size > 0) result = result.filter(row => allowed.has(getColValue(row, key)));
    });

    // Column text filters — text search (high-cardinality: NIK, Nama, ID)
    Object.entries(textColumnFilters).forEach(([key, text]) => {
      if (text.trim()) {
        const lower = text.toLowerCase();
        result = result.filter(row => getColValue(row, key).toLowerCase().includes(lower));
      }
    });

    // Sort ascending by skorKesejahteraan to show lowest welfare first
    result.sort((a, b) => a.skorKesejahteraan - b.skorKesejahteraan);

    // Generic Sort
    if (sortConfig) {
      result.sort((a, b) => {
        let valA: string | number = "";
        let valB: string | number = "";

        const tahapOrder: Record<string, number> = {
          proses: 0, analisis: 1, validasi: 2, diterima: 3, ditolak: 4,
        };

        const key = sortConfig.key;
        if (key === "id_keluarga") { valA = a.idLabel; valB = b.idLabel; }
        else if (key === "bantuan") { valA = a.bantuan ? a.bantuan.join(", ") : ""; valB = b.bantuan ? b.bantuan.join(", ") : ""; }
        else if (key === "tahap") { valA = tahapOrder[a.tahap] || 99; valB = tahapOrder[b.tahap] || 99; }
        else if (key === "skor_aspd") { valA = a.skorASPD ?? 0; valB = b.skorASPD ?? 0; }
        else if (key === "skor_pkh_plus") { valA = a.skorPKHPlus ?? a.skorPKHT ?? 0; valB = b.skorPKHPlus ?? b.skorPKHT ?? 0; }
        else {
          const rawValA = a[key as keyof DataRow];
          const rawValB = b[key as keyof DataRow];
          valA = typeof rawValA === "number" ? rawValA : String(rawValA ?? "");
          valB = typeof rawValB === "number" ? rawValB : String(rawValB ?? "");
        }

        const isNum = isNumericColumn(sortConfig.key);
        if (valA === undefined || valA === null) valA = isNum ? 0 : "";
        if (valB === undefined || valB === null) valB = isNum ? 0 : "";

        if (typeof valA === "string" && typeof valB === "string") {
          return sortConfig.direction === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
        } else {
          return sortConfig.direction === "asc"
            ? valA > valB ? 1 : valA < valB ? -1 : 0
            : valB > valA ? 1 : valB < valA ? -1 : 0;
        }
      });
    }

    return result;
  }, [
    displayData, activeTab, searchTerm, filterKecamatan, filterKelurahan,
    filterOverlap, selectedDesils, sortConfig, columnFilters, textColumnFilters,
  ]);

  // Pagination
  const totalPages = Math.max(
    1,
    serverTotalPages,
  );
  const paginatedData = filteredData;

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
    console.log(`[runAnalisisAndAdvance] Memulai asesmen komprehensif untuk ID: ${id}`);
    const res = await apiFetch(`/api/v1/asesmen/komprehensif/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error(`[runAnalisisAndAdvance] Asesmen komprehensif gagal untuk ID: ${id}.`, err);
      throw new Error(err.detail || "Gagal menjalankan analisis.");
    }

    const hasil = await res.json().catch(() => ({}));
    console.log(`[runAnalisisAndAdvance] Hasil asesmen komprehensif diterima untuk ID: ${id}.`, hasil);
    const bantuan = Array.isArray(hasil?.hasil_analisis_sosial_tim3?.hasil_rekomendasi_final)
      ? hasil.hasil_analisis_sosial_tim3.hasil_rekomendasi_final
      : [];
    const bantuanEligible = bantuan.filter(
      (item: string | null | undefined) => item && item !== "Tidak Eligible",
    );
    const nextStatus = bantuanEligible.length > 0 ? "validasi" : "ditolak";

    console.log(`[runAnalisisAndAdvance] Memperbarui status ID: ${id} menjadi "${nextStatus}" dengan bantuan:`, bantuanEligible);
    const resUpdate = await apiFetch(`/api/v1/manajemen-bantuan/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status_validasi: nextStatus,
        bantuan: bantuanEligible,
      }),
    });
    if (!resUpdate.ok) {
      const err = await resUpdate.json().catch(() => ({}));
      console.error(`[runAnalisisAndAdvance] Gagal memperbarui status ke database untuk ID: ${id}.`, err);
      throw new Error(err.detail || "Gagal memperbarui tahap hasil analisis.");
    }
    console.log(`[runAnalisisAndAdvance] Sukses memproses dan memperbarui status ID: ${id}`);
  };

  const handleAnalisis = async (id: string) => {
    console.log(`[handleAnalisis] Trigger analisis manual untuk ID: ${id}`);
    setProcessingIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
    try {
      await runAnalisisAndAdvance(id);
      await fetchData(); // refresh data setelah AI selesai
      console.log(`[handleAnalisis] Sukses menyelesaikan analisis manual untuk ID: ${id}`);
    } catch (e) {
      console.error(`[handleAnalisis] Terjadi kesalahan saat analisis ID: ${id}.`, e);
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
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
    console.log(`[handleBatchAnalisis] Memulai batch analisis untuk ${selectedRows.size} record:`, Array.from(selectedRows));
    setIsBatchAnalyzing(true);
    setBatchProgress(0);
    const ids = Array.from(selectedRows);
    const total = ids.length;
    let processed = 0;

    for (const id of ids) {
      try {
        console.log(`[handleBatchAnalisis] [${processed + 1}/${total}] Menganalisis ID: ${id}`);
        await runAnalisisAndAdvance(id);
      } catch (e) {
        console.error(`[handleBatchAnalisis] Gagal menganalisis ID: ${id}. Error:`, e);
      }
      processed++;
      setBatchProgress(Math.round((processed / total) * 100));
    }

    await fetchData();
    setIsBatchAnalyzing(false);
    setSelectedRows(new Set());
    setBatchProgress(0);
    console.log(`[handleBatchAnalisis] Batch analisis selesai.`);
  };

  const handleAnalisisAll = async () => {
    if (isBatchAnalyzing) return;
    console.log(`[handleAnalisisAll] Memulai Analisis Semua data di background server`);
    setIsBatchAnalyzing(true);
    try {
      const res = await apiFetch(`/api/v1/asesmen/batch-all`, { method: "POST" });
      if (!res.ok) throw new Error("Gagal memulai batch-all");
      const data = await res.json();
      console.log(`[handleAnalisisAll] Respons server:`, data);
      alert("Proses analisis massal telah dimulai di background server. Silakan refresh halaman secara berkala untuk melihat perubahan.");
    } catch (e) {
      console.error(`[handleAnalisisAll] Gagal:`, e);
      alert("Gagal memulai analisis massal.");
    } finally {
      setIsBatchAnalyzing(false);
      await fetchData();
    }
  };

  const resetFilters = () => {
    setSearchTerm("");
    setFilterKecamatan("Semua");
    setFilterKelurahan("Semua");
    setSelectedDesils([]);
    setFilterOverlap("Semua");
    setSortConfig(null);
    setColumnFilters({});
    setTextColumnFilters({});
  };

  const resetColumns = () => {
    setVisibleColumns(new Set(COLUMNS.filter(c => c.defaultVisible || c.locked).map(c => c.key)));
  };

  const uniqueColumnValues = useMemo(() => {
    const result: Record<string, string[]> = {};
    COLUMNS.forEach(col => {
      if (col.key === 'aksi') return;
      const set = new Set<string>();
      data.forEach(row => set.add(getColValue(row, col.key)));
      result[col.key] = Array.from(set).sort((a, b) =>
        a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
      );
    });
    return result;
  }, [data]);

  const openFilter = (colKey: string) => {
    const isHighCard = HIGH_CARDINALITY_COLS.has(colKey);
    if (isHighCard) {
      setPendingTextFilter(textColumnFilters[colKey] || '');
    } else {
      const allVals = uniqueColumnValues[colKey] || [];
      const existing = columnFilters[colKey];
      setPendingFilter(existing && existing.size > 0 ? new Set(existing) : new Set(allVals));
    }
    setFilterDropdownSearch('');
    setOpenFilterCol(prev => prev === colKey ? null : colKey);
  };

  const applyFilter = (colKey: string) => {
    const isHighCard = HIGH_CARDINALITY_COLS.has(colKey);
    if (isHighCard) {
      setTextColumnFilters(prev => {
        const next = { ...prev };
        if (!pendingTextFilter.trim()) delete next[colKey];
        else next[colKey] = pendingTextFilter.trim();
        return next;
      });
    } else {
      const allVals = uniqueColumnValues[colKey] || [];
      setColumnFilters(prev => {
        const next = { ...prev };
        if (pendingFilter.size === 0 || pendingFilter.size >= allVals.length) { delete next[colKey]; }
        else { next[colKey] = new Set(pendingFilter); }
        return next;
      });
    }
    setOpenFilterCol(null);
  };

  const renderExcelHeader = (label: string, colKey: string) => {
    const isOpen = openFilterCol === colKey;
    const isHighCard = HIGH_CARDINALITY_COLS.has(colKey);
    const hasTextFilter = !!(textColumnFilters[colKey]?.trim());
    const hasCheckboxFilter = !!(columnFilters[colKey] && columnFilters[colKey].size > 0);
    const hasFilter = isHighCard ? hasTextFilter : hasCheckboxFilter;
    const isSortActive = sortConfig?.key === colKey;
    const isNum = isNumericColumn(colKey);
    const allVals = uniqueColumnValues[colKey] || [];
    const filteredVals = filterDropdownSearch
      ? allVals.filter(v => v.toLowerCase().includes(filterDropdownSearch.toLowerCase()))
      : allVals;
    const displayVals = filteredVals.slice(0, MAX_CHECKBOX_VALUES);
    const allPendingSelected = displayVals.length > 0 && displayVals.every(v => pendingFilter.has(v));

    return (
      <th key={colKey} className={`excel-filter-th${isSortActive ? ' sort-active' : ''}`} style={{ position: 'relative', padding: 0, minWidth: '120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 8px 12px 14px', gap: '4px' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: hasFilter || isSortActive ? '#2563eb' : '#475569', whiteSpace: 'nowrap' }}>
            {label}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '2px', flexShrink: 0 }}>
            {isSortActive && <span style={{ color: '#2563eb', display: 'flex' }}>{sortConfig?.direction === 'asc' ? <ChevronUp size={11} /> : <ChevronDown size={11} />}</span>}
            <button
              onClick={(e) => { e.stopPropagation(); openFilter(colKey); }}
              style={{ background: hasFilter ? '#eff6ff' : 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', display: 'flex', alignItems: 'center', borderRadius: '3px', color: hasFilter ? '#2563eb' : '#94a3b8' }}
              title={hasFilter ? 'Filter aktif' : 'Filter kolom'}
            >
              <Filter size={11} />
            </button>
          </div>
        </div>
        {isOpen && (
          <div className="excel-filter-dropdown" onClick={e => e.stopPropagation()}>
            {/* Sort section — selalu tampil */}
            <div className="efd-sort-section">
              <button className={`efd-sort-btn${isSortActive && sortConfig?.direction === 'asc' ? ' active' : ''}`}
                onClick={() => setSortConfig({ key: colKey, direction: 'asc' })}>
                {isNum ? '↑ Terkecil ke Terbesar' : '↑ A ke Z'}
              </button>
              <button className={`efd-sort-btn${isSortActive && sortConfig?.direction === 'desc' ? ' active' : ''}`}
                onClick={() => setSortConfig({ key: colKey, direction: 'desc' })}>
                {isNum ? '↓ Terbesar ke Terkecil' : '↓ Z ke A'}
              </button>
              {isSortActive && (
                <button className="efd-sort-btn efd-clear-sort" onClick={() => setSortConfig(null)}>✕ Hapus Urutan</button>
              )}
            </div>
            <div className="efd-divider" />

            {isHighCard ? (
              /* ── Mode Text Search untuk kolom high-cardinality (NIK, Nama, ID) ── */
              <>
                <div className="efd-highcard-label">Cari (mengandung teks):</div>
                <div className="efd-search" style={{ borderBottom: 'none', paddingBottom: '4px' }}>
                  <Search size={11} />
                  <input
                    placeholder={`Ketik ${label}...`}
                    value={pendingTextFilter}
                    onChange={e => setPendingTextFilter(e.target.value)}
                    onClick={e => e.stopPropagation()}
                    onKeyDown={e => e.key === 'Enter' && applyFilter(colKey)}
                    autoFocus
                  />
                  {pendingTextFilter && (
                    <button onClick={() => setPendingTextFilter('')}
                      style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0 2px', display: 'flex' }}>
                      <XCircle size={11} />
                    </button>
                  )}
                </div>
                {hasTextFilter && (
                  <div style={{ padding: '2px 12px 6px', fontSize: '11px', color: '#60a5fa' }}>
                    Filter aktif: "{textColumnFilters[colKey]}"
                  </div>
                )}
              </>
            ) : (
              /* ── Mode Checkbox untuk kolom kategorikal ── */
              <>
                <div className="efd-search">
                  <Search size={11} />
                  <input placeholder="Cari nilai..." value={filterDropdownSearch}
                    onChange={e => setFilterDropdownSearch(e.target.value)}
                    onClick={e => e.stopPropagation()} autoFocus />
                </div>
                <div className="efd-list">
                  <label className="efd-item efd-select-all">
                    <input type="checkbox" checked={allPendingSelected}
                      onChange={() => {
                        if (allPendingSelected) setPendingFilter(prev => { const n = new Set(prev); displayVals.forEach(v => n.delete(v)); return n; });
                        else setPendingFilter(prev => new Set([...prev, ...displayVals]));
                      }} />
                    <span>(Pilih Semua{filteredVals.length > MAX_CHECKBOX_VALUES ? ` — ${MAX_CHECKBOX_VALUES} dari ${filteredVals.length}` : ''})</span>
                  </label>
                  {displayVals.map(v => (
                    <label key={v} className="efd-item">
                      <input type="checkbox" checked={pendingFilter.has(v)}
                        onChange={() => setPendingFilter(prev => { const n = new Set(prev); n.has(v) ? n.delete(v) : n.add(v); return n; })} />
                      <span>{v}</span>
                    </label>
                  ))}
                  {filteredVals.length > MAX_CHECKBOX_VALUES && (
                    <div style={{ padding: '6px 12px', fontSize: '11px', color: '#94a3b8', fontStyle: 'italic' }}>
                      +{filteredVals.length - MAX_CHECKBOX_VALUES} nilai lainnya tidak ditampilkan
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="efd-actions">
              <button className="efd-btn-ok" onClick={() => applyFilter(colKey)}>OK</button>
              <button className="efd-btn-cancel" onClick={() => setOpenFilterCol(null)}>Batal</button>
            </div>
          </div>
        )}
      </th>
    );
  };

  const colCount =
    1 + // checkbox
    COLUMNS.filter((c) => visibleColumns.has(c.key) || c.locked).length;

  const filteredColumns = COLUMNS.filter((col) =>
    col.label.toLowerCase().includes(searchColumn.toLowerCase())
  );

  return (
    <AdminLayout title="Manajemen Bantuan" onLogout={onLogout}>
      <div className="mb-page-wrapper">
        {/* ── Header ────────────────────────── */}
        <div className="mb-header">
          <div className="mb-title-area">
            <h3>Manajemen Bantuan</h3>
            <p>
              Kelola seluruh eligible bantuan sosial mulai dari tahap
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
                tabCounts.analisis === 0
              }
              style={{
                opacity:
                  tabCounts.analisis === 0
                    ? 0.5
                    : 1,
              }}
            >
              <BrainCircuit size={16} /> Analisis Semua ({tabCounts.analisis})
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

                  <div className="mb-column-search">
                    <input
                      type="text"
                      placeholder="Cari kolom..."
                      value={searchColumn}
                      onChange={(e) => setSearchColumn(e.target.value)}
                    />
                  </div>

                  <div className="mb-popover-list" style={{ maxHeight: "300px", overflowY: "auto" }}>
                    {filteredColumns.map((col) => {
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
                    return renderExcelHeader(col.label, col.key);
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
                  paginatedData.map((row) => {
                    const displayRow = processingIds.has(row.id_keluarga)
                      ? { ...row, tahap: "proses" as Tahap }
                      : row;

                    return (
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
                          {displayRow.tahap === "analisis" ? (
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
                            case "nama": {
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
                            }
                            case "wilayah": {
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
                            }
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
                                  {displayRow.tahap === "proses" || displayRow.tahap === "analisis"
                                    ? "—"
                                    : (row.skorASPD ?? 0).toFixed(1)}
                                </td>
                              );
                            case "skor_pkh_plus":
                              return (
                                <td key={col.key} style={{ padding: "14px 16px", fontWeight: 600, color: "#7c3aed" }}>
                                  {displayRow.tahap === "proses" || displayRow.tahap === "analisis"
                                    ? "—"
                                    : (row.skorPKHPlus ?? row.skorPKHT ?? 0).toFixed(1)}
                                </td>
                              );
                            case "tahap":
                              return (
                                <td key={col.key} style={{ padding: "14px 16px" }}>
                                  <span className={`mb-stage-badge ${getStageBadgeClass(displayRow.tahap)}`} style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                                    <span className="mb-badge-dot" />
                                    {getStageBadgeLabel(displayRow.tahap)}
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
                                    {displayRow.tahap === "proses" && (
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

                                    {displayRow.tahap === "analisis" && (
                                      <button
                                        className="mb-btn-analisis"
                                        style={{
                                          width: "120px",
                                          display: "inline-flex",
                                          alignItems: "center",
                                          justifyContent: "center",
                                          gap: "6px",
                                        }}
                                        disabled={processingIds.has(row.id_keluarga)}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleAnalisis(row.id_keluarga);
                                        }}
                                      >
                                        {processingIds.has(row.id_keluarga) ? (
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

                                    {displayRow.tahap === "validasi" && (
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

                                    {(displayRow.tahap === "diterima" || displayRow.tahap === "ditolak") && (
                                      <button
                                        className="mb-btn-review"
                                        style={{
                                          width: "120px",
                                          display: "inline-flex",
                                          alignItems: "center",
                                          justifyContent: "center",
                                          gap: "6px",
                                          backgroundColor: displayRow.tahap === "diterima" ? "#ecfdf5" : "#fef2f2",
                                          color: displayRow.tahap === "diterima" ? "#10b981" : "#ef4444",
                                          borderColor: displayRow.tahap === "diterima" ? "#a7f3d0" : "#fecaca",
                                        }}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          navigate(`/detail-hasil/${row.id_keluarga}`, {
                                            state: row,
                                          });
                                        }}
                                      >
                                        {displayRow.tahap === "diterima" ? <CheckCircle size={14} /> : <FileBarChart size={14} />} Review
                                      </button>
                                    )}
                                  </div>
                                </td>
                              );
                            default: {
                              const val = displayRow[col.key as keyof DataRow];
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
                          }
                        })}
                      </tr>
                    );
                  })
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
                  {Math.min(currentPage * ITEMS_PER_PAGE, serverTotalItems)}
                </strong>{" "}
                dari <strong>{serverTotalItems}</strong> data keluarga
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
