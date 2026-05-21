import React, { useState, useRef, useEffect } from 'react';
import { ShieldCheck, ChevronDown, X, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, UserCog } from 'lucide-react';
import { updateMyProfile, type UpdateProfilePayload } from '../../services/api';

interface HeaderProps {
  title?: string;
}

const Header: React.FC<HeaderProps> = ({
  title = 'Dashboard Monitoring',
}) => {
  const username = localStorage.getItem('username') || 'User';
  const role = localStorage.getItem('role') || 'ANALIS';
  const initials = username.slice(0, 2).toUpperCase();
  const isAdmin = role === 'ADMIN';

  // ── Dropdown state ──────────────────────────────────────────────────────────
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // ── Modal state ──────────────────────────────────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [form, setForm] = useState<UpdateProfilePayload>({
    username: username,
    email: '',
    new_password: '',
  });

  // ── Tutup dropdown saat klik di luar ─────────────────────────────────────────
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ── Buka modal edit ───────────────────────────────────────────────────────────
  const openEditModal = () => {
    setForm({ username, email: '', new_password: '' });
    setFormError('');
    setShowNewPw(false);
    setDropdownOpen(false);
    setModalOpen(true);
  };

  // ── Submit edit profil ────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!form.username?.trim()) {
      setFormError('Username tidak boleh kosong.');
      return;
    }
    if (form.new_password && form.new_password.length < 6) {
      setFormError('Password baru minimal 6 karakter.');
      return;
    }

    // Hanya kirim field yang berubah
    const payload: UpdateProfilePayload = {};
    if (form.username && form.username !== username) payload.username = form.username;
    if (form.email?.trim()) payload.email = form.email;
    if (form.new_password?.trim()) payload.new_password = form.new_password;

    if (Object.keys(payload).length === 0) {
      setFormError('Tidak ada perubahan yang perlu disimpan.');
      return;
    }

    setIsSubmitting(true);
    setFormError('');
    try {
      const updated = await updateMyProfile(payload);
      // Perbarui localStorage
      localStorage.setItem('username', updated.username);
      localStorage.setItem('role', updated.role);
      setModalOpen(false);
      showToast('success', 'Profil berhasil diperbarui! Halaman akan diperbarui...');
      setTimeout(() => window.location.reload(), 1500);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Terjadi kesalahan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <>
      {/* Toast */}
      {toast && (
        <div className={`header-toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{toast.message}</span>
        </div>
      )}

      <header className="header">
        <h2>{title}</h2>

        {/* User Profile — klik untuk dropdown */}
        <div className="user-profile-wrapper" ref={dropdownRef}>
          <button
            className="user-profile-btn"
            onClick={() => setDropdownOpen(v => !v)}
            aria-haspopup="true"
            aria-expanded={dropdownOpen}
          >
            <div className="user-info">
              <span className="user-name">{username}</span>
              {/* Pill badge sama seperti di Pengaturan */}
              <span className={`header-role-badge ${isAdmin ? 'badge-role-admin' : 'badge-role-analyst'}`}>
                {role}
              </span>
            </div>
            <div className={`user-avatar ${isAdmin ? 'avatar-admin-header' : ''}`} title={username}>
              {isAdmin
                ? <ShieldCheck size={17} />
                : <span className="avatar-initials">{initials}</span>
              }
            </div>
            <ChevronDown
              size={14}
              className={`dropdown-chevron ${dropdownOpen ? 'rotated' : ''}`}
            />
          </button>

          {/* Dropdown */}
          {dropdownOpen && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-header">
                <div className={`dropdown-avatar ${isAdmin ? 'avatar-admin-header' : ''}`}>
                  {isAdmin ? <ShieldCheck size={20} /> : <span>{initials}</span>}
                </div>
                <div>
                  <div className="dropdown-username">{username}</div>
                  <span className={`header-role-badge ${isAdmin ? 'badge-role-admin' : 'badge-role-analyst'}`}>
                    {role}
                  </span>
                </div>
              </div>
              <div className="profile-dropdown-divider" />
              <button className="profile-dropdown-item" onClick={openEditModal}>
                <UserCog size={15} />
                <span>Edit Profil</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ── Modal Edit Profil ──────────────────────────────────────────────── */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <UserCog size={20} className="text-blue-600" />
                <h4>Edit Profil Akun</h4>
              </div>
              <button className="btn-close-modal" onClick={() => setModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              {formError && (
                <div className="form-error-banner">
                  <AlertCircle size={15} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Username</label>
                <input
                  type="text"
                  className="config-input"
                  value={form.username || ''}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  placeholder="Username baru"
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email baru <span style={{ color: '#9ca3af', fontWeight: 400 }}>(opsional)</span></label>
                <input
                  type="email"
                  className="config-input"
                  value={form.email || ''}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  placeholder="Kosongkan jika tidak ingin diubah"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password baru <span style={{ color: '#9ca3af', fontWeight: 400 }}>(opsional)</span></label>
                <div className="input-password-wrapper">
                  <input
                    type={showNewPw ? 'text' : 'password'}
                    className="config-input"
                    value={form.new_password || ''}
                    onChange={e => setForm(f => ({ ...f, new_password: e.target.value }))}
                    placeholder="Minimal 6 karakter"
                  />
                  <button
                    type="button"
                    className="btn-toggle-password"
                    onClick={() => setShowNewPw(v => !v)}
                    tabIndex={-1}
                  >
                    {showNewPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setModalOpen(false)} disabled={isSubmitting}>Batal</button>
              <button className="btn-primary" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting
                  ? <><Loader2 size={14} className="spin-icon" /> Menyimpan...</>
                  : 'Simpan Perubahan'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;
