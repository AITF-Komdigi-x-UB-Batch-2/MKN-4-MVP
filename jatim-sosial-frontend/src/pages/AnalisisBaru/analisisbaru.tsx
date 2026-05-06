import React from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/layout/AdminLayout';
import { 
  CheckCircle, 
  UploadCloud, 
  BrainCircuit,
  FileSpreadsheet,
  Info,
  Download
} from 'lucide-react';
import './AnalisisBaru.css';

interface AnalisisBaruProps {
  onLogout?: () => void;
}

const AnalisisBaru: React.FC<AnalisisBaruProps> = ({ onLogout }) => {
  const navigate = useNavigate();

  return (
    <AdminLayout title="Import Data" onLogout={onLogout}>
      <div className="analisis-page-wrapper">
        
        {/* Header */}
        <div className="analisis-page-header">
          <div>
            <h3 className="section-title">Import Data untuk Analisis</h3>
            <p className="section-subtitle">Unggah file Excel atau CSV yang berisi data keluarga untuk diproses oleh sistem AI.</p>
          </div>
        </div>

        {/* Import Content */}
        <div className="analisis-content-split">
          <div className="analisis-left-col">
            <div className="import-container">

              {/* Upload Dropzone */}
              <div className="upload-dropzone large">
                <div className="upload-icon-wrapper">
                  <UploadCloud size={52} className="upload-icon" />
                </div>
                <h4>Unggah File Data Excel / CSV</h4>
                <p>Tarik &amp; lepaskan file di sini, atau klik tombol di bawah untuk memilih file dari perangkat Anda.</p>
                <input type="file" id="file-upload" accept=".xlsx,.xls,.csv" style={{ display: 'none' }} />
                <label htmlFor="file-upload" className="browse-btn">
                  <FileSpreadsheet size={16} /> Pilih File
                </label>
                <span className="upload-hint">Format yang didukung: .xlsx, .xls, .csv — Maks. 10MB</span>
              </div>

              {/* Template Download */}
              <div className="template-download-card">
                <div className="template-icon-wrap">
                  <Download size={20} color="#2563eb" />
                </div>
                <div className="template-info">
                  <strong>Unduh Template Standar</strong>
                  <p>Pastikan file Anda mengikuti format kolom yang telah ditentukan sistem agar proses analisis berjalan optimal.</p>
                </div>
                <button className="template-btn">
                  Unduh Template
                </button>
              </div>

              {/* Info Box */}
              <div className="info-box blue">
                <Info size={15} />
                <span>
                  <strong>Catatan:</strong> Pastikan setiap baris mewakili satu keluarga dan semua kolom wajib telah diisi sebelum mengunggah file. Data yang tidak lengkap akan dilewati secara otomatis oleh sistem.
                </span>
              </div>

            </div>
          </div>
        </div>

      </div>

      {/* Fixed Bottom Action Bar */}
      <div className="bottom-action-bar">
        <div className="action-status">
          <CheckCircle size={20} className="text-green" />
          <span>UNGGAH FILE UNTUK MEMULAI PROSES ANALISIS AI</span>
        </div>
        <button className="process-submit-btn" onClick={() => navigate('/detail-hasil/1')}>
          <BrainCircuit size={18} />
          Proses Analisis AI
        </button>
      </div>
    </AdminLayout>
  );
};

export default AnalisisBaru;
