import React from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "../../components/layout/AdminLayout";
import {
  CheckCircle,
  AlertCircle,
  UploadCloud,
  FileSpreadsheet,
  Info,
  Download,
  Loader,
} from "lucide-react";
import "./AnalisisBaru.css";
import { useState, useRef, useEffect } from "react";

interface AnalisisBaruProps {
  onLogout?: () => void;
}

const AnalisisBaru: React.FC<AnalisisBaruProps> = ({ onLogout }) => {
  const navigate = useNavigate();
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState("Menghubungkan ke server...");
  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const xhrRef = useRef<XMLHttpRequest | null>(null);
  const intervalRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (xhrRef.current) {
        xhrRef.current.abort();
      }
    };
  }, []);

  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        setUploadError("File terlalu besar. Maksimal 10MB.");
        return;
      }
      setUploadedFile(file);
      setUploadError(null);
    }
  };

  const handleUpload = async () => {
    if (!uploadedFile) {
      setUploadError("Pilih file terlebih dahulu");
      return;
    }

    setIsLoading(true);
    setUploadError(null);
    setUploadProgress(0);
    setProgressStatus("Menghubungkan ke server...");

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      let currentProgress = 0;
      let backendCompleted = false;
      let backendResult: any = null;
      let uploadErrorOccurred: Error | null = null;

      if (intervalRef.current) clearInterval(intervalRef.current);
      if (xhrRef.current) xhrRef.current.abort();

      const progressInterval = setInterval(() => {
        if (uploadErrorOccurred) {
          clearInterval(progressInterval);
          intervalRef.current = null;
          xhrRef.current = null;
          setIsLoading(false);
          setUploadError(uploadErrorOccurred.message);
          showToast("error", uploadErrorOccurred.message);
          return;
        }

        if (backendCompleted) {
          // Accelerate to 100%
          currentProgress += 10;
          if (currentProgress >= 100) {
            currentProgress = 100;
            clearInterval(progressInterval);
            intervalRef.current = null;
            xhrRef.current = null;
            setUploadProgress(100);
            setProgressStatus("Selesai! Data berhasil diimport.");
            
            const pesan = backendResult?.pesan || "Import berhasil.";
            showToast("success", pesan);
            setIsLoading(false);
            setTimeout(() => navigate("/manajemen-bantuan"), 1500);
          } else {
            setUploadProgress(currentProgress);
          }
        } else {
          // Smooth crawl to 90%
          if (currentProgress < 75) {
            currentProgress += Math.floor(Math.random() * 4) + 3; // Increment by 3-6%
            setProgressStatus("Mengirim file...");
          } else if (currentProgress < 95) {
            currentProgress += 1; // Slow down near the end
            setProgressStatus("Memproses & memvalidasi data...");
          }
          setUploadProgress(Math.min(95, currentProgress));
        }
      }, 70);

      intervalRef.current = progressInterval;

      // Start actual request
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/v1/import-csv", true);
      xhr.withCredentials = true;
      xhr.timeout = 180000; // 3 minutes timeout

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            backendResult = JSON.parse(xhr.responseText);
          } catch (e) {
            backendResult = { pesan: "Import berhasil." };
          }
          backendCompleted = true;
        } else {
          try {
            const resData = JSON.parse(xhr.responseText);
            uploadErrorOccurred = new Error(resData.detail || resData.pesan || `Upload gagal dengan status ${xhr.status}`);
          } catch (e) {
            uploadErrorOccurred = new Error(`Upload gagal dengan status ${xhr.status}`);
          }
        }
      };

      xhr.onerror = () => {
        uploadErrorOccurred = new Error("Koneksi jaringan error. Upload gagal.");
      };

      xhr.ontimeout = () => {
        uploadErrorOccurred = new Error("Batas waktu pengunggahan terlampaui (Timeout). Silakan coba lagi.");
      };

      xhrRef.current = xhr;
      xhr.send(formData);

    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan saat upload";
      showToast("error", message);
      setUploadError(message);
      setIsLoading(false);
    }
  };

  return (
    <AdminLayout title="Import Data" onLogout={onLogout}>
      {toast && (
        <div className={`notification-toast ${toast.type}`}>
          {toast.type === "success" ? (
            <CheckCircle size={20} />
          ) : (
            <AlertCircle size={20} />
          )}
          <span>{toast.message}</span>
        </div>
      )}
      <div className="analisis-page-wrapper">
        {/* Header */}
        <div className="analisis-page-header">
          <div>
            <h3 className="section-title">Import Data untuk Analisis</h3>
            <p className="section-subtitle">
              Unggah file Excel atau CSV yang berisi data keluarga untuk
              diproses oleh sistem AI.
            </p>
          </div>
        </div>

        {/* Import Content */}
        <div className="analisis-content-split">
          <div className="analisis-left-col">
            <div className="import-container">
              {/* Upload Dropzone */}
              <div className={`upload-dropzone large ${isLoading ? "loading" : ""}`}>
                {isLoading ? (
                  <div className="upload-loading-container">
                    <div className="upload-loading-spinner">
                      <Loader size={48} className="upload-spin" />
                    </div>
                    <h4 className="upload-loading-title">{progressStatus}</h4>
                    <p className="upload-loading-desc">
                      Mohon tunggu, jangan tutup halaman ini.
                    </p>
                    
                    <div className="mb-upload-progress-wrapper upload-progress-container">
                      <div className="mb-upload-progress-info">
                        <span>Status Progres</span>
                        <strong>{uploadProgress}%</strong>
                      </div>
                      <div className="mb-upload-progress-track">
                        <div
                          className="mb-upload-progress-fill"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="upload-icon-wrapper">
                      <UploadCloud size={52} className="upload-icon" />
                    </div>
                    <h4>Unggah File Data Excel / CSV</h4>
                    <p>
                      Tarik &amp; lepaskan file di sini, atau klik tombol di bawah
                      untuk memilih file dari perangkat Anda.
                    </p>
                    <input
                      type="file"
                      id="file-upload"
                      accept=".xlsx,.xls,.csv"
                      style={{ display: "none" }}
                      onChange={handleFileSelect}
                    />
                    <label htmlFor="file-upload" className="browse-btn">
                      <FileSpreadsheet size={16} /> Pilih File
                    </label>
                    <span className="upload-hint">
                      Format yang didukung: .xlsx, .xls, .csv — Maks. 10MB
                    </span>
                    {uploadedFile && (
                      <p
                        style={{
                          marginTop: "10px",
                          color: "#10b981",
                          fontWeight: "bold",
                        }}
                      >
                        ✓ File dipilih: {uploadedFile.name}
                      </p>
                    )}
                  </>
                )}
              </div>

              {/* Template Download */}
              <div className="template-download-card">
                <div className="template-icon-wrap">
                  <Download size={20} color="#2563eb" />
                </div>
                <div className="template-info">
                  <strong>Unduh Template Standar</strong>
                  <p>
                    Pastikan file Anda mengikuti format kolom yang telah
                    ditentukan sistem agar proses analisis berjalan optimal.
                  </p>
                </div>
                <button className="template-btn">Unduh Template</button>
              </div>

              {/* Info Box */}
              <div className="info-box blue">
                <Info size={15} />
                <span>
                  <strong>Catatan:</strong> Pastikan setiap baris mewakili satu
                  keluarga dan semua kolom wajib telah diisi sebelum mengunggah
                  file. Data yang tidak lengkap akan dilewati secara otomatis
                  oleh sistem.
                </span>
              </div>

              {uploadError && (
                <div
                  className="info-box"
                  style={{ borderColor: "#ef4444", backgroundColor: "#fee2e2" }}
                >
                  <Info size={15} style={{ color: "#ef4444" }} />
                  <span style={{ color: "#991b1b" }}>
                    <strong>Kesalahan:</strong> {uploadError}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Action Bar */}
      <div className="bottom-action-bar">
        <div className="action-status">
          {isLoading ? (
            <>
              <Loader
                size={20}
                className="text-blue"
                style={{ animation: "spin 1s linear infinite" }}
              />
              <span>MEMPROSES UPLOAD...</span>
            </>
          ) : uploadedFile ? (
            <>
              <CheckCircle size={20} className="text-green" />
              <span>SIAP UNTUK UNGGAH</span>
            </>
          ) : (
            <>
              <CheckCircle size={20} className="text-green" />
              <span>UNGGAH FILE UNTUK MEMULAI PROSES ANALISIS AI</span>
            </>
          )}
        </div>
        {uploadedFile && (
          <button
            onClick={handleUpload}
            disabled={isLoading}
            style={{
              padding: "10px 24px",
              backgroundColor: isLoading ? "#9ca3af" : "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: isLoading ? "not-allowed" : "pointer",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {isLoading ? <Loader size={18} /> : null}
            {isLoading ? "Uploading..." : "Upload & Lanjut"}
          </button>
        )}
      </div>
    </AdminLayout>
  );
};

export default AnalisisBaru;
