import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, EyeOff, Eye, LogIn, ShieldAlert } from 'lucide-react';
import './Login.css';
import logoJatim from '../../assets/Lambang_Provinsi_Jawa_Timur.svg';

interface LoginProps {
  onLogin?: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Username dan password harus diisi!');
      return;
    }
    
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Login gagal, periksa kembali kredensial Anda');
      }
      
      // Simpan JWT token
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', data.username);
      localStorage.setItem('role', data.role || 'ANALIS');
      
      if (onLogin) onLogin();
      navigate('/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo & Agency Title */}
        <div className="login-header">
          <img
            src={logoJatim}
            alt="Logo Jawa Timur"
            className="login-logo"
          />
          <h1 className="login-agency">Pemetaan Kemiskinan dan Bantuan</h1>
          <p className="login-agency-sub">DISKOMINFO JATIM</p>
        </div>

        <div className="login-divider"></div>

        {/* System Title */}
        <div className="login-system-header">
          <h2 className="login-system-title">Masuk ke Sistem</h2>
          <p className="login-system-desc">
            Sistem Pendukung Keputusan Bantuan Sosial<br />
            Provinsi Jawa Timur
          </p>
        </div>

        {/* Login Form */}
        <form className="login-form" onSubmit={handleLogin}>
          {errorMsg && (
            <div style={{ backgroundColor: '#fef2f2', color: '#ef4444', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px', fontWeight: 500, border: '1px solid #fca5a5' }}>
              {errorMsg}
            </div>
          )}
          <div className="form-group">
            <label htmlFor="username">Nama Pengguna atau Email</label>
            <div className="input-wrapper">
              <User className="input-icon" size={20} />
              <input
                type="text"
                id="username"
                placeholder="Masukkan username atau email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Kata Sandi</label>
            <div className="input-wrapper">
              <Lock className="input-icon" size={20} />
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                placeholder="Masukkan kata sandi"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="icon-button"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <Eye size={20} /> : <EyeOff size={20} />}
              </button>
            </div>
          </div>

          <div className="form-actions-row">
            <label className="checkbox-container">
              <input type="checkbox" />
              <span className="checkmark"></span>
              Ingat Saya
            </label>
            <a href="#" className="forgot-password">Lupa Kata Sandi?</a>
          </div>

          <button type="submit" className="login-submit-btn" disabled={isLoading}>
            {isLoading ? 'Memvalidasi...' : 'Masuk ke Sistem'}
            {!isLoading && <LogIn size={18} className="btn-icon" />}
          </button>
        </form>

        {/* Footer Warning */}
        <div className="login-warning">
          <ShieldAlert className="warning-icon" size={24} />
          <div className="warning-text">
            <strong>Peringatan Keamanan:</strong>
            <p>Hanya untuk penggunaan internal pemerintah provinsi Jawa Timur. Seluruh aktivitas dalam sistem ini dipantau untuk tujuan keamanan dan audit.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
