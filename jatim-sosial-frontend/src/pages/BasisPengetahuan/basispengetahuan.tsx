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



export default BasisPengetahuan;
