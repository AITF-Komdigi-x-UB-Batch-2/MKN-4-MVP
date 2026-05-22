import React, { useState } from 'react';
import AdminLayout from '../../components/layout/AdminLayout';
import { 
  Search, 
  ChevronRight, 
  FileText, 
  Download
} from 'lucide-react';
import SideDrawer from '../../components/ui/SideDrawer';
import './BasisPengetahuan.css';

interface BasisPengetahuanProps {
  onLogout?: () => void;
}

interface PolicyDocument {
  id: string;
  title: string;
  description: string;
  kategori: string;
  kategoriColorClass: string;
  tanggal: string;
  masaBerlaku: string;
  unit: string;
  size: string;
  aiSummary: string;
}

const mockDocuments: PolicyDocument[] = [
  {
    id: '1',
    title: 'Juklak ASPD Tahun 2026',
    description: 'Petunjuk Pelaksanaan Asistensi Sosial Penyandang Disabilitas (ASPD) Tahun 2026',
    kategori: 'ASPD',
    kategoriColorClass: 'kategori-sk',
    tanggal: '25 Feb 2026',
    masaBerlaku: 'S/D Dicabut',
    unit: 'Dinas Sosial',
    size: '11.7 MB',
    aiSummary: 'Petunjuk pelaksanaan Asistensi Sosial Penyandang Disabilitas (ASPD) Provinsi Jawa Timur Tahun 2026 yang mengatur kriteria penerima, mekanisme penyaluran, dan tata cara monitoring bantuan bagi penyandang disabilitas.',
  },
  {
    id: '2',
    title: 'Juknis PKH Plus 2026',
    description: 'Petunjuk Teknis Program Keluarga Harapan (PKH) Plus Provinsi Jawa Timur Tahun 2026',
    kategori: 'PKH PLUS',
    kategoriColorClass: 'kategori-pergub',
    tanggal: '01 Jan 2026',
    masaBerlaku: 'S/D Dicabut',
    unit: 'Dinas Sosial',
    size: '1.9 MB',
    aiSummary: 'Petunjuk teknis pelaksanaan PKH Plus Tahun 2026 di Jawa Timur, berfokus pada pemberian bantuan sosial tambahan bagi lanjut usia dalam keluarga sangat miskin.',
  },
  {
    id: '3',
    title: 'Juknis Kemiskinan Ekstrem',
    description: 'Petunjuk Teknis Penyelenggaraan Percepatan Penghapusan Kemiskinan Ekstrem',
    kategori: 'KEMISKINAN EKSTREM',
    kategoriColorClass: 'kategori-ingub',
    tanggal: '13 Jan 2025',
    masaBerlaku: 'S/D Dicabut',
    unit: 'BAPPEDA',
    size: '1.6 MB',
    aiSummary: 'Pedoman operasional verifikasi, validasi, dan koordinasi lintas sektor untuk percepatan penghapusan kemiskinan ekstrem di Provinsi Jawa Timur.',
  },
  {
    id: '4',
    title: 'Juknis KIP KPM Jawara',
    description: 'Petunjuk Teknis Kartu Indonesia Pintar (KIP) Keluarga Penerima Manfaat (KPM) Jawara',
    kategori: 'KIP KPM JAWARA',
    kategoriColorClass: 'kategori-se',
    tanggal: '10 Jan 2026',
    masaBerlaku: 'S/D Dicabut',
    unit: 'Dinas Pendidikan',
    size: '6.0 MB',
    aiSummary: 'Panduan juknis Kartu Indonesia Pintar khusus untuk anak-anak dari Keluarga Penerima Manfaat (KPM) peserta program Jatim Jawara.',
  },
  {
    id: '5',
    title: 'Juknis KIP Putri Jawara',
    description: 'Petunjuk Teknis Kartu Indonesia Pintar (KIP) Putri Jawara',
    kategori: 'KIP PUTRI JAWARA',
    kategoriColorClass: 'kategori-se',
    tanggal: '12 Jan 2026',
    masaBerlaku: 'S/D Dicabut',
    unit: 'Dinas Pendidikan',
    size: '5.9 MB',
    aiSummary: 'Panduan juknis Kartu Indonesia Pintar (KIP) Putri Jawara untuk mendukung keberlanjutan pendidikan anak perempuan berprestasi dari keluarga rentan.',
  },
  {
    id: '6',
    title: 'Juknis KIP PPKS Jawara',
    description: 'Petunjuk Teknis Kartu Indonesia Pintar (KIP) Pemerlu Pelayanan Kesejahteraan Sosial (PPKS) Jawara',
    kategori: 'KIP PPKS JAWARA',
    kategoriColorClass: 'kategori-se',
    tanggal: '15 Jan 2026',
    masaBerlaku: 'S/D Dicabut',
    unit: 'Dinas Sosial',
    size: '10.2 MB',
    aiSummary: 'Petunjuk teknis pemberian beasiswa Kartu Indonesia Pintar (KIP) bagi anak-anak PPKS (Pemerlu Pelayanan Kesejahteraan Sosial) di Provinsi Jawa Timur.',
  }
];

const BasisPengetahuan: React.FC<BasisPengetahuanProps> = ({ onLogout }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<PolicyDocument | null>(null);

  return (
    <AdminLayout title="Basis Pengetahuan" onLogout={onLogout}>
      <div className={`bp-page-wrapper ${selectedDoc ? 'panel-open' : ''}`}>
        
        {/* Main Content Area */}
        <div className="bp-main-content">
          <div className="bp-header">
            <h3>Basis Pengetahuan</h3>
            <p>Pusat repositori kebijakan dan regulasi bantuan sosial Pemerintah Provinsi Jawa Timur.</p>
          </div>

          {/* Search Box */}
          <div className="search-container">
            <Search className="search-icon" size={20} />
            <input 
              type="text" 
              placeholder="Cari dokumen, regulasi, atau kata kunci kebijakan..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Table List */}
          <div className="bp-table-card">
            <table className="bp-table">
              <thead>
                <tr>
                  <th>NAMA DOKUMEN</th>
                  <th>KATEGORI</th>
                  <th>TANGGAL TERBIT</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {mockDocuments
                  .filter(doc => 
                    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    doc.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    doc.kategori.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((doc) => (
                    <tr 
                      key={doc.id} 
                      className={selectedDoc?.id === doc.id ? 'active-row' : ''}
                      onClick={() => setSelectedDoc(doc)}
                    >
                      <td>
                        <div className="doc-title-cell">
                          <FileText size={20} className="doc-icon-blue" />
                          <div>
                            <div className="doc-title-text">{doc.title}</div>
                            <div className="doc-desc-text">{doc.description}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`kategori-badge ${doc.kategoriColorClass}`}>
                          {doc.kategori}
                        </span>
                      </td>
                      <td className="doc-date-text">{doc.tanggal}</td>
                      <td className="text-right">
                        <ChevronRight size={18} className="text-gray-400" />
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
            
            <div className="bp-pagination">
              <span className="pagination-text">Menampilkan 1-6 dari 6 dokumen</span>
              <div className="pagination-actions">
                <button className="btn-page-sm"><ChevronLeft size={16} /></button>
                <button className="btn-page-sm"><ChevronRight size={16} /></button>
              </div>
            </div>
          </div>

        </div>

        {/* Right Side Panel / Drawer */}
        <SideDrawer 
          isOpen={!!selectedDoc} 
          onClose={() => setSelectedDoc(null)} 
          title="Detail Kebijakan"
          width="400px"
        >
          {selectedDoc && (
            <>
              {/* Document Identity Card */}
              <div className="doc-identity-card">
                <FileText size={48} className="doc-icon-large" />
                <h3 className="doc-id-title">{selectedDoc.title}</h3>
                <p className="doc-id-desc">{selectedDoc.description}</p>
              </div>

              <button className="btn-download-pdf">
                <Download size={18} /> Unduh Dokumen (PDF)
              </button>

              {/* Information Grid */}
              <div className="info-main-label">INFORMASI UTAMA</div>
              <div className="info-grid">
                <div className="info-grid-item">
                  <span className="info-item-label">DITERBITKAN</span>
                  <span className="info-item-value">{selectedDoc.tanggal}</span>
                </div>
                <div className="info-grid-item">
                  <span className="info-item-label">MASA BERLAKU</span>
                  <span className="info-item-value">{selectedDoc.masaBerlaku}</span>
                </div>
                <div className="info-grid-item">
                  <span className="info-item-label">UNIT PENGUSUL</span>
                  <span className="info-item-value">{selectedDoc.unit}</span>
                </div>
                <div className="info-grid-item">
                  <span className="info-item-label">UKURAN FILE</span>
                  <span className="info-item-value">{selectedDoc.size}</span>
                </div>
              </div>
            </>
          )}
        </SideDrawer>

      </div>
    </AdminLayout>
  );
};

// Quick fix for missing ChevronLeft inside component
const ChevronLeft = ({size}: {size: number}) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
);

export default BasisPengetahuan;
