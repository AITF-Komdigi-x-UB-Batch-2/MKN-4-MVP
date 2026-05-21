import React, { useState, useEffect, useCallback } from 'react';
import AdminLayout from '../../components/layout/AdminLayout';
import {
  UserPlus,
  Users,
  X,
  Trash2,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Eye,
  EyeOff
} from 'lucide-react';
import './Pengaturan.css';
import {
  fetchUsers,
  createUser,
  deleteUser,
  updateUserStatus,
  type UserData,
  type CreateUserPayload
} from '../../services/api';

interface PengaturanProps {
  onLogout?: () => void;
}

type Role = 'ANALIS' | 'ADMIN';



const getInitials = (username: string) =>
  username.slice(0, 2).toUpperCase();

const Pengaturan: React.FC<PengaturanProps> = ({ onLogout }) => {
  // Ambil info user yang sedang login
  const currentUsername = localStorage.getItem('username') || '';
  const currentRole = localStorage.getItem('role') || 'ANALIS';
  const isAdmin = currentRole === 'ADMIN';

  const [users, setUsers] = useState<UserData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UserData | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Form state
  const [form, setForm] = useState<CreateUserPayload>({
    username: '',
    email: '',
    password: '',
    role: 'ANALIS',
  });
  const [formError, setFormError] = useState<string>('');

  // ── Load users ──────────────────────────────────────────────────────────────
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch (err: unknown) {
      showToast('error', err instanceof Error ? err.message : 'Gagal memuat data pengguna.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // ── Toast helper ─────────────────────────────────────────────────────────────
  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  // ── Modal helpers ─────────────────────────────────────────────────────────────
  const openModalNewUser = () => {
    setForm({ username: '', email: '', password: '', role: 'ANALIS' });
    setFormError('');
    setShowPassword(false);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormError('');
  };

  // ── Create User ───────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    // Validasi lokal
    if (!form.username.trim()) { setFormError('Username wajib diisi.'); return; }
    if (!form.email.trim()) { setFormError('Email wajib diisi.'); return; }
    if (!form.password || form.password.length < 6) { setFormError('Password minimal 6 karakter.'); return; }

    setIsSubmitting(true);
    setFormError('');
    try {
      const newUser = await createUser(form);
      setUsers(prev => [...prev, newUser]);
      closeModal();
      showToast('success', `Pengguna '${newUser.username}' berhasil ditambahkan!`);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Terjadi kesalahan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Delete User ───────────────────────────────────────────────────────────────
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await deleteUser(deleteTarget.id);
      setUsers(prev => prev.filter(u => u.id !== deleteTarget.id));
      showToast('success', `Pengguna '${deleteTarget.username}' berhasil dihapus.`);
    } catch (err: unknown) {
      showToast('error', err instanceof Error ? err.message : 'Gagal menghapus pengguna.');
    } finally {
      setDeleteTarget(null);
    }
  };

  // ── Toggle Active ─────────────────────────────────────────────────────────────
  const handleToggleActive = async (user: UserData) => {
    try {
      const updated = await updateUserStatus(user.id, { is_active: !user.is_active });
      setUsers(prev => prev.map(u => u.id === user.id ? updated : u));
      showToast('success', `Status pengguna '${user.username}' diperbarui.`);
    } catch (err: unknown) {
      showToast('error', err instanceof Error ? err.message : 'Gagal memperbarui status.');
    }
  };

  // ── Role Badge ────────────────────────────────────────────────────────────────
  const getRoleBadgeClass = (role: Role) => {
    switch (role) {
      case 'ANALIS': return 'badge-role-analyst';
      case 'ADMIN': return 'badge-role-admin';
      default: return '';
    }
  };

  return (
    <AdminLayout title="Pengaturan Sistem" onLogout={onLogout}>
      <div className="pengaturan-page-wrapper">

        {/* Toast Notification */}
        {toast && (
          <div className={`toast-notification ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
            {toast.type === 'success'
              ? <CheckCircle2 size={18} />
              : <AlertCircle size={18} />
            }
            <span>{toast.message}</span>
          </div>
        )}

        {/* Header Section */}
        <div className="pengaturan-header">
          <div className="pengaturan-title-area">
            <h3>Pengaturan Sistem</h3>
            <p>Kelola aksesibilitas personil dan konfigurasi parameter pendukung keputusan AI.</p>
          </div>
          <div className="flex-center gap-3">
            <button className="btn-secondary-sm" onClick={loadUsers} title="Refresh daftar user">
              <RefreshCw size={15} />
            </button>
            {/* Tombol tambah hanya untuk ADMIN */}
            {isAdmin && (
              <button className="btn-primary" onClick={openModalNewUser}>
                <UserPlus size={16} /> Tambah Pengguna Baru
              </button>
            )}
          </div>
        </div>

        {/* User Management Table */}
        <div className="settings-card">
          <div className="settings-card-header flex-between">
            <div className="flex-center gap-2">
              <Users size={18} className="text-blue-600" />
              <h4 className="font-semibold text-gray-800 m-0">Daftar Pengguna Aktif</h4>
              <span className="user-count-badge">{users.length}</span>
            </div>
          </div>

          <div className="table-responsive">
            {isLoading ? (
              <div className="loading-state">
                <Loader2 size={28} className="spin-icon" />
                <p>Memuat data pengguna...</p>
              </div>
            ) : users.length === 0 ? (
              <div className="empty-state">
                <Users size={40} className="text-gray-300" />
                <p>Belum ada pengguna terdaftar.</p>
              </div>
            ) : (
              <table className="user-table">
                <thead>
                  <tr>
                    <th>NAMA PENGGUNA</th>
                    <th>USERNAME</th>
                    <th>ROLE</th>
                    <th>ALAMAT EMAIL</th>
                    <th>STATUS</th>
                    <th>AKSI</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id} className={!user.is_active ? 'row-inactive' : ''}>
                      <td>
                        <div className="user-profile-cell">
                          <div className={`avatar-circle ${user.role === 'ADMIN' ? 'avatar-admin' : ''}`}>
                            {user.role === 'ADMIN'
                              ? <ShieldCheck size={16} />
                              : getInitials(user.username)
                            }
                          </div>
                          <span className="font-semibold text-gray-900">{user.username}</span>
                        </div>
                      </td>
                      <td className="text-gray-500 font-mono text-sm">@{user.username}</td>
                      <td>
                        <span className={`role-badge ${getRoleBadgeClass(user.role as Role)}`}>{user.role}</span>
                      </td>
                      <td className="text-gray-500">{user.email}</td>
                      <td>
                        {/* Toggle status: hanya admin, dan bukan akun sendiri */}
                        {isAdmin && user.username !== currentUsername ? (
                          <button
                            className={`status-toggle ${user.is_active ? 'active' : 'inactive'}`}
                            onClick={() => handleToggleActive(user)}
                            title={user.is_active ? 'Klik untuk nonaktifkan' : 'Klik untuk aktifkan'}
                          >
                            <span className={`dot ${user.is_active ? 'green' : 'gray'}`}></span>
                            <span>{user.is_active ? 'Aktif' : 'Nonaktif'}</span>
                          </button>
                        ) : (
                          <div className="status-indicator">
                            <span className={`dot ${user.is_active ? 'green' : 'gray'}`}></span>
                            <span className={user.is_active ? 'text-green-600 font-medium' : 'text-gray-500 font-medium'}>
                              {user.is_active ? 'Aktif' : 'Nonaktif'}
                            </span>
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="action-cell">
                          {/* Tombol hapus: hanya admin, bukan akun sendiri, bukan akun ADMIN lain */}
                          {isAdmin && user.username !== currentUsername && user.role !== 'ADMIN' ? (
                            <button
                              className="btn-icon-danger"
                              onClick={() => setDeleteTarget(user)}
                              title="Hapus pengguna"
                            >
                              <Trash2 size={15} />
                            </button>
                          ) : (
                            <span className="no-action-label" title={
                              !isAdmin ? 'Hanya admin yang bisa menghapus'
                              : user.username === currentUsername ? 'Tidak bisa menghapus akun sendiri'
                              : 'Tidak bisa menghapus akun ADMIN'
                            }>—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="pagination-wrapper border-t border-gray-200">
            <div className="pagination-info">
              Menampilkan {users.length} dari {users.length} pengguna
            </div>
          </div>
        </div>



      </div>

      {/* ── Modal Tambah Pengguna ─────────────────────────────────────────── */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="flex-center gap-2">
                <UserPlus size={20} className="text-blue-600" />
                <h4>Tambah Pengguna Baru</h4>
              </div>
              <button className="btn-close-modal" onClick={closeModal}><X size={20} /></button>
            </div>
            <div className="modal-body">

              {formError && (
                <div className="form-error-banner">
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Nama / Username <span className="required">*</span></label>
                  <input
                    type="text"
                    className="config-input"
                    value={form.username}
                    onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                    placeholder="cth: analis_jatim"
                    autoFocus
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Role <span className="required">*</span></label>
                  <select
                    className="config-input"
                    value={form.role}
                    onChange={e => setForm(f => ({ ...f, role: e.target.value as 'ADMIN' | 'ANALIS' }))}
                  >
                    {/* Admin hanya bisa membuat akun ANALIS */}
                    <option value="ANALIS">ANALIS</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Email <span className="required">*</span></label>
                <input
                  type="email"
                  className="config-input"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  placeholder="cth: analis@dinsos.go.id"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password <span className="required">*</span></label>
                <div className="input-password-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className="config-input"
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="Minimal 6 karakter"
                  />
                  <button
                    type="button"
                    className="btn-toggle-password"
                    onClick={() => setShowPassword(v => !v)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeModal} disabled={isSubmitting}>Batal</button>
              <button className="btn-primary" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? (
                  <><Loader2 size={15} className="spin-icon" /> Menyimpan...</>
                ) : (
                  <><UserPlus size={15} /> Tambah Pengguna</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Konfirmasi Hapus ─────────────────────────────────────────────── */}
      {deleteTarget && (
        <div className="modal-overlay" onClick={() => setDeleteTarget(null)}>
          <div className="modal-container modal-sm" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h4 className="text-red-600">Hapus Pengguna</h4>
              <button className="btn-close-modal" onClick={() => setDeleteTarget(null)}><X size={20} /></button>
            </div>
            <div className="modal-body">
              <div className="delete-confirm-body">
                <div className="delete-icon-wrap">
                  <Trash2 size={28} className="text-red-500" />
                </div>
                <p>Apakah Anda yakin ingin menghapus pengguna</p>
                <p className="delete-target-name">@{deleteTarget.username}</p>
                <p className="delete-warning">Tindakan ini tidak dapat dibatalkan.</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setDeleteTarget(null)}>Batal</button>
              <button className="btn-danger" onClick={handleDeleteConfirm}>
                <Trash2 size={15} /> Ya, Hapus
              </button>
            </div>
          </div>
        </div>
      )}

    </AdminLayout>
  );
};

export default Pengaturan;
