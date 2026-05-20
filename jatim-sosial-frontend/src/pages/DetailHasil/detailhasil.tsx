import React, { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { rawKeluargaData } from '../../data/dataKeluarga';
import { mockData, type Tahap } from '../../data/mockData';
import AdminLayout from '../../components/layout/AdminLayout';
import { RecommendationCard } from '../../components/cards/RecommendationCard';
import {
  BarChart2,
  CheckCircle,
  BrainCircuit,
  Home,
  RefreshCw,
  ShieldCheck,
  User,
  ThumbsUp,
  AlertCircle
} from 'lucide-react';
import './DetailHasil.css';

interface DetailHasilProps {
  onLogout?: () => void;
}

const DetailHasil: React.FC<DetailHasilProps> = ({ onLogout }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // React State for interactive MVP transitions
  const [stageState, setStageState] = useState<Tahap>(location.state?.tahap || 'analisis');
  const currentTahap = stageState;

  const desil = location.state?.desil || 1;
  const bantuanDariState = location.state?.bantuan || ['PKH'];
  const namaKeluarga = location.state?.nama || 'Bpk. Lailatur Coder';
  const nik = location.state?.nik || '35780120010002';
  const wilayah = location.state?.wilayah || 'Surabaya';
  const kecamatan = location.state?.kecamatan || 'Wonokromo';
  const tanggal = location.state?.tanggal || '24 Okt 2023';

  const rawData = rawKeluargaData.find(k => k.id_keluarga === location.state?.id_keluarga) || rawKeluargaData[0];

  const familyId = location.state?.id_keluarga || id || 'FAM-001';
  const matchingMock = mockData.find(m => m.id_keluarga === familyId) || mockData[0];
  const skorKesejahteraan = location.state?.skorKesejahteraan !== undefined ? location.state.skorKesejahteraan : (matchingMock?.skorKesejahteraan || 0.15);

  const [selectedPrograms, setSelectedPrograms] = useState<string[]>(
    currentTahap !== 'analisis' ? bantuanDariState : []
  );
  const [isConfirming, setIsConfirming] = useState(false);
  const isFinalized = currentTahap !== 'analisis';
  const [successMsg, setSuccessMsg] = useState('');
  const [isAssistanceConfirmed, setIsAssistanceConfirmed] = useState(currentTahap !== 'analisis');

  // Exact same score mappings as in Manajemen Bantuan page
  const getFamilyScores = (famId: string) => {
    switch (famId) {
      case 'FAM-001': return { aspd: 85.4, pkht: 92.1 };
      case 'FAM-002': return { aspd: 82.1, pkht: 35.0 };
      case 'FAM-003': return { aspd: 40.5, pkht: 35.2 };
      case 'FAM-004': return { aspd: 95.2, pkht: 91.0 };
      case 'FAM-005': return { aspd: 38.0, pkht: 88.0 };
      case 'FAM-006': return { aspd: 86.4, pkht: 82.1 };
      case 'FAM-007': return { aspd: 98.5, pkht: 94.2 };
      case 'FAM-008': return { aspd: 32.3, pkht: 89.4 };
      case 'FAM-009': return { aspd: 89.1, pkht: 35.0 };
      case 'FAM-010': return { aspd: 34.0, pkht: 31.5 };
      case 'FAM-011': return { aspd: 35.5, pkht: 80.2 };
      case 'FAM-012': return { aspd: 83.0, pkht: 31.5 };
      case 'FAM-013': return { aspd: 38.0, pkht: 82.5 };
      default: return { aspd: 95.0, pkht: 90.0 };
    }
  };

  const familyScores = getFamilyScores(familyId);

  const recommendations: any[] = [
    {
      id: 'ASPD',
      title: 'ASPD (Asistensi Sosial Penyandang Disabilitas)',
      match: familyScores.aspd,
      desc: 'Bantuan sosial tunai untuk penyandang disabilitas berat guna pemenuhan kebutuhan dasar.',
      reason: 'Keluarga memenuhi kriteria prioritas dengan skor kelayakan tinggi.',
      isReceived: false
    },
    {
      id: 'PKHT',
      title: 'PKHT (Program Keluarga Harapan Tematik)',
      match: familyScores.pkht,
      desc: 'Bantuan bersyarat terintegrasi untuk keluarga miskin dengan kluster khusus/tematik tertentu.',
      reason: 'Analisis kriteria kesehatan dan pendidikan menunjukkan kelayakan tinggi.',
      isReceived: false
    },
    {
      id: 'KE',
      title: 'KE (Kemandirian Ekonomi / UEP)',
      match: 40,
      desc: 'Bantuan modal usaha ekonomi produktif untuk pemberdayaan ekonomi keluarga.',
      reason: 'Potensi pengembangan usaha mikro mandiri.',
      isReceived: false
    },
    {
      id: 'JAWARA',
      title: 'Jawara',
      match: 0,
      desc: 'Bantuan pemberdayaan khusus untuk kelompok masyarakat rentan Jawa Timur.',
      reason: 'Tidak ada data indikator yang terpenuhi',
      isReceived: false
    },
    {
      id: 'JAWARA P',
      title: 'Jawara P',
      match: 0,
      desc: 'Program pemberdayaan perempuan kepala keluarga Jawa Timur (Jawara Perempuan).',
      reason: 'Tidak ada data indikator yang terpenuhi',
      isReceived: false
    },
    {
      id: 'PPU',
      title: 'PPU (Pemberdayaan Perempuan Usaha)',
      match: 0,
      desc: 'Bantuan stimulus modal usaha untuk pemberdayaan perempuan pelaku usaha mikro.',
      reason: 'Tidak ada data indikator yang terpenuhi',
      isReceived: false
    }
  ];

  const familyRecs = location.state?.rekomendasiBantuan || matchingMock?.rekomendasiBantuan || [];

  const filteredRecommendations = recommendations.filter(rec => {
    return familyRecs.includes(rec.id);
  });

  const otherRecommendations = recommendations.filter(rec => {
    return !familyRecs.includes(rec.id);
  });

  const handleToggleProgram = (id: string) => {
    if (isFinalized || isAssistanceConfirmed) return;

    setSelectedPrograms(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const handleConfirmAssistance = () => {
    if (selectedPrograms.length === 0) return;

    setIsConfirming(true);
    setTimeout(() => {
      setIsConfirming(false);
      const item = mockData.find(m => m.id_keluarga === familyId);
      if (item) {
        item.tahap = 'validasi';
        item.bantuan = selectedPrograms;
      }
      setStageState('validasi');
      setSuccessMsg('Rekomendasi bantuan berhasil diajukan ke tahap Validasi!');
      setTimeout(() => setSuccessMsg(''), 2000);
    }, 1200);
  };

  const handleSupervisorApprove = () => {
    const item = mockData.find(m => m.id_keluarga === familyId);
    if (item) {
      item.tahap = 'diterima';
      item.bantuan = selectedPrograms;
    }
    setStageState('diterima');
    setSuccessMsg('Bantuan Sosial Berhasil Disetujui!');
    setTimeout(() => setSuccessMsg(''), 2000);
  };

  const handleSupervisorReject = () => {
    const item = mockData.find(m => m.id_keluarga === familyId);
    if (item) {
      item.tahap = 'ditolak';
    }
    setStageState('ditolak');
    setSuccessMsg('Pengajuan Bantuan Sosial Ditolak!');
    setTimeout(() => setSuccessMsg(''), 2000);
  };

  const handleReanalyze = () => {
    const item = mockData.find(m => m.id_keluarga === familyId);
    if (item) {
      item.tahap = 'analisis';
    }
    setStageState('analisis');
    setSuccessMsg('Status dikembalikan ke tahap Analisis!');
    setTimeout(() => setSuccessMsg(''), 2000);
  };

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
            <p className="subtitle-family">ID / NIK: {nik} • Kecamatan {kecamatan}, {wilayah} • Data per {tanggal}</p>
          </div>
          <div className="header-actions">
            <button className="btn-primary" onClick={() => navigate(`/detail-keluarga/${id || 1}`)}>
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

          {/* Left Column (Main Analysis Data) */}
          <div className="detail-main-col">


            {/* Validator / Validasi Section */}
            <div className="detail-card-section">
              <div className="detail-card-header">
                <Home size={18} className="text-blue" />
                <h4>Validator / Validasi</h4>
              </div>
              <div className="detail-card-body">
                {/* Foto Centered */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
                  <div className="visual-image-wrapper" style={{ width: '60%', maxWidth: '500px' }}>
                    <div className="placeholder-image">
                      <Home size={48} className="text-gray-400" />
                      <span className="img-caption">Foto Survey Hunian Lapangan</span>
                    </div>
                  </div>
                </div>

                {/* Tabel 4x4 Bersih: Variabel, Data DTKS, Status, Alasan */}
                <div className="table-responsive" style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', marginBottom: '0px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#475569' }}>VARIABEL</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#475569' }}>DATA REGISTER</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#475569' }}>STATUS</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#475569' }}>ALASAN DETEKSI</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                        <td style={{ padding: '14px 16px', fontWeight: 600, color: '#1e293b' }}>Atap</td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>Seng</td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{ 
                            display: 'inline-block',
                            width: '100px',
                            textAlign: 'center',
                            padding: '6px 0', 
                            borderRadius: '9999px', 
                            fontSize: '11px', 
                            fontWeight: 700, 
                            backgroundColor: '#fef2f2', 
                            color: '#ef4444' 
                          }}>
                            Tidak Match
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>
                          Foto menunjukkan penutup atap berupa genteng tanah liat, bukan seng.
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                        <td style={{ padding: '14px 16px', fontWeight: 600, color: '#1e293b' }}>Dinding</td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>Tembok</td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{ 
                            display: 'inline-block',
                            width: '100px',
                            textAlign: 'center',
                            padding: '6px 0', 
                            borderRadius: '9999px', 
                            fontSize: '11px', 
                            fontWeight: 700, 
                            backgroundColor: '#ecfdf5', 
                            color: '#10b981' 
                          }}>
                            Match
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>
                          Foto mengonfirmasi dinding terbuat dari tembok batu bata yang diplester halus.
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: '14px 16px', fontWeight: 600, color: '#1e293b' }}>Lantai</td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>Keramik</td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{ 
                            display: 'inline-block',
                            width: '100px',
                            textAlign: 'center',
                            padding: '6px 0', 
                            borderRadius: '9999px', 
                            fontSize: '11px', 
                            fontWeight: 700, 
                            backgroundColor: '#fef2f2', 
                            color: '#ef4444' 
                          }}>
                            Tidak Match
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>
                          Foto mendeteksi lantai berbahan granit/marmer premium berwarna putih mengilap.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>


            {/* Smart Recommendations Section */}
            {currentTahap !== 'diterima' && (
              <div className="recommendations-container">
                <h3 className="section-title-large">Rekomendasi Utama (Analisis AI)</h3>
                <div className="recommendation-cards-grid" style={{ marginBottom: '28px' }}>
                  {filteredRecommendations.length === 0 ? (
                    <div style={{ gridColumn: '1 / -1', padding: '32px 24px', backgroundColor: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '12px', textAlign: 'center', color: '#64748b' }}>
                      <AlertCircle size={32} style={{ margin: '0 auto 8px', color: '#94a3b8' }} />
                      <p style={{ fontWeight: 600, fontSize: '14px', color: '#334155' }}>Tidak Ada Rekomendasi Program Bantuan</p>
                      <p style={{ fontSize: '12px', marginTop: '4px', color: '#64748b' }}>Keluarga ini tidak memenuhi indikasi kelayakan untuk program ASPD, PKHT, atau KE.</p>
                    </div>
                  ) : (
                    filteredRecommendations.map(rec => (
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

                <h3 className="section-title-large" style={{ marginTop: '28px' }}>Program Bantuan Lainnya (Pilihan Alternatif)</h3>
                <div className="recommendation-cards-grid">
                  {otherRecommendations.length === 0 ? (
                    <p style={{ color: '#94a3b8', fontSize: '13px' }}>Tidak ada pilihan program bantuan lainnya.</p>
                  ) : (
                    otherRecommendations.map(rec => (
                      <RecommendationCard
                        key={rec.id}
                        data={{
                          ...rec,
                          match: 0 // Menjamin kartu putih premium
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
            {selectedPrograms.length > 0 && currentTahap !== 'diterima' && (
              <div 
                className={`selected-assistance-section ${isFinalized ? 'finalized' : (isAssistanceConfirmed ? 'finalized' : '')}`}
                style={isAssistanceConfirmed && !isFinalized ? { borderColor: '#bbf7d0', backgroundColor: '#f0fdf4' } : {}}
              >
                <div className="flex-between max-w-full">
                  <div>
                    <h4>
                      {isFinalized 
                        ? 'Bantuan yang Akan Diterima (Disetujui)' 
                        : (isAssistanceConfirmed ? 'Bantuan Terkonfirmasi (Belum Dikirim)' : 'Bantuan yang Akan Diterima')}
                    </h4>
                    <p>Program yang dipilih: {selectedPrograms.map(id => recommendations.find(r => r.id === id)?.title || id).join(', ')}</p>
                  </div>
                  {!isFinalized && (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {isAssistanceConfirmed ? (
                        <>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#16a34a', fontWeight: 600, fontSize: '13px', background: '#dcfce7', padding: '6px 12px', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
                            <CheckCircle size={14} /> Terkonfirmasi
                          </span>
                          <button
                            className="btn-outline"
                            onClick={() => setIsAssistanceConfirmed(false)}
                            style={{ padding: '6px 12px', fontSize: '13px' }}
                          >
                            Ubah Bantuan
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn-confirm-assistance"
                          onClick={() => setIsAssistanceConfirmed(true)}
                          style={{ padding: '8px 16px', fontSize: '13px' }}
                        >
                          Konfirmasi Bantuan
                        </button>
                      )}
                    </div>
                  )}
                  {isFinalized && (
                    <span className="badge-final"><CheckCircle size={16} /> Final Decision</span>
                  )}
                </div>
              </div>
            )}

          </div>

          {/* Right Column (Dynamic Panel based on Tahap) */}
          <div className="detail-side-col">

            {/* PANEL: ANALISIS */}
            {currentTahap === 'analisis' && (
              <div className="validation-panel">
                <div className="panel-header">
                  <ShieldCheck size={18} className="text-blue" />
                  <h4>Analisis Petugas</h4>
                </div>
                <div className="panel-body">
                  <div className="form-group">
                    <label>Catatan Analisis</label>
                    <textarea
                      placeholder="Tambahkan observasi lapangan atau catatan analisis..."
                      rows={5}
                    ></textarea>
                  </div>
                  <div className="panel-actions" style={{ flexDirection: 'column' }}>
                    <button
                      className="btn-action approve w-full"
                      style={{ justifyContent: 'center' }}
                      onClick={handleConfirmAssistance}
                      disabled={!isAssistanceConfirmed || isConfirming}
                    >
                      <CheckCircle size={18} /> {isConfirming ? 'Memproses...' : 'Kirim ke Tahap Validasi'}
                    </button>
                    {!isAssistanceConfirmed && (
                      <p style={{ fontSize: '12px', color: '#dc2626', textAlign: 'center', margin: 0, fontWeight: 500 }}>
                        {!selectedPrograms.length 
                          ? 'Pilih minimal satu program terlebih dahulu.' 
                          : 'Konfirmasikan program pilihan Anda di bawah terlebih dahulu.'}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}             {/* PANEL: VALIDASI */}
            {currentTahap === 'validasi' && (
              <div className="validation-panel">
                <div className="panel-header">
                  <ShieldCheck size={18} className="text-orange" />
                  <h4>Validasi Supervisor</h4>
                </div>
                <div className="panel-body">
                  <div className="mb-4">
                    <label style={{ fontSize: '12px', fontWeight: 600, color: '#6b7280' }}>DIBUAT OLEH (PETUGAS)</label>
                    <p style={{ fontSize: '14px', background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>Keluarga layak mendapatkan bantuan sosial berdasarkan pertimbangan desil kesejahteraan desil {desil} dan kecocokan verifikasi visual.</p>
                  </div>
                  <div className="form-group">
                    <label>Catatan Supervisor / Catatan Validasi</label>
                    <textarea
                      placeholder="Masukkan catatan keputusan validasi supervisor..."
                      rows={4}
                    ></textarea>
                  </div>
                  <div className="panel-actions" style={{ flexDirection: 'column', gap: '8px' }}>
                    <button className="btn-action approve w-full" style={{ justifyContent: 'center' }} onClick={handleSupervisorApprove}>
                      <ThumbsUp size={18} /> Setujui Bantuan
                    </button>
                    <button className="btn-action reject w-full" style={{ justifyContent: 'center', backgroundColor: '#fff1f2', color: '#be123c', border: '1px solid #fda4af' }} onClick={handleSupervisorReject}>
                      <RefreshCw size={18} /> Tolak Pengajuan
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* PANEL: DITERIMA */}
            {currentTahap === 'diterima' && (
              <div className="validation-panel">
                <div className="panel-header" style={{ backgroundColor: '#f0fdfa' }}>
                  <CheckCircle size={18} className="text-teal" style={{ color: '#0d9488' }} />
                  <h4 style={{ color: '#0d9488' }}>Pengajuan Disetujui</h4>
                </div>
                <div className="panel-body">
                  <p style={{ fontSize: '14px', lineHeight: 1.5, color: '#374151', marginBottom: '16px' }}>
                    Keluarga ini telah disetujui untuk menerima program bantuan sosial berikut berdasarkan analisis kebutuhan dan kelayakan ekonomi desil {desil}.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedPrograms.map(prog => (
                      <div key={prog} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', background: '#f0fdf4', borderRadius: '6px', border: '1px solid #bbf7d0', color: '#15803d', fontWeight: 600, fontSize: '13px' }}>
                        <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#16a34a' }}></span>
                        {recommendations.find(r => r.id === prog)?.title || prog}
                      </div>
                    ))}
                    {selectedPrograms.length === 0 && (
                      <div style={{ fontSize: '13px', color: '#6b7280', fontStyle: 'italic', textAlign: 'center', padding: '10px' }}>
                        Tidak ada program bantuan spesifik yang dipilih
                      </div>
                    )}
                  </div>
                  <button className="btn-action w-full" style={{ justifyContent: 'center', marginTop: '16px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }} onClick={() => navigate('/manajemen-bantuan')}>
                    Kembali ke Daftar
                  </button>
                </div>
              </div>
            )}

            {/* PANEL: DITOLAK */}
            {currentTahap === 'ditolak' && (
              <div className="validation-panel">
                <div className="panel-header" style={{ backgroundColor: '#fef2f2' }}>
                  <AlertCircle size={18} className="text-red" style={{ color: '#dc2626' }} />
                  <h4 style={{ color: '#dc2626' }}>Pengajuan Bantuan Ditolak</h4>
                </div>
                <div className="panel-body">
                  <p style={{ fontSize: '14px', lineHeight: 1.5, color: '#374151', marginBottom: '16px' }}>
                    Berdasarkan kriteria kemiskinan dan proses verifikasi supervisor, keluarga ini dinilai tidak memenuhi kriteria kelayakan sebagai penerima manfaat.
                  </p>
                  <div className="panel-actions" style={{ flexDirection: 'column', gap: '10px' }}>
                    <button className="btn-action w-full" style={{ justifyContent: 'center', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' }} onClick={handleReanalyze}>
                      <RefreshCw size={14} /> Analisis Ulang Data
                    </button>
                    <button className="btn-action w-full" style={{ justifyContent: 'center', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }} onClick={() => navigate('/manajemen-bantuan')}>
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
