/**
 * Interceptor API Fetch
 * Membungkus fungsi fetch bawaan browser agar otomatis:
 * 1. Menambahkan Authorization Bearer header jika token tersedia di localStorage.
 * 2. Mengarahkan URL relative ke endpoint proxy.
 */

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  try {
    const headers = new Headers(options.headers || {});
    
    // Khusus untuk JSON (jika tipe konten tidak didefinisikan secara manual)
    if (!headers.has('Content-Type') && !(options.body instanceof FormData || options.body instanceof URLSearchParams)) {
      headers.set('Content-Type', 'application/json');
    }

    let response = await fetch(endpoint, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Cegah infinite loop jika request /login atau /refresh yang 401
      if (!endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh') && !endpoint.includes('/login')) {
        try {
          const refreshRes = await fetch('/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          if (refreshRes.ok) {
            // Lakukan retry request asli (cookie baru otomatis terkirim oleh browser)
            response = await fetch(endpoint, {
              ...options,
              headers,
            });
          } else {
            throw new Error('Refresh token gagal atau kadaluarsa');
          }
        } catch (refreshErr) {
          console.warn("Silent refresh gagal, mengarahkan ke login:", refreshErr);
          localStorage.removeItem('access_token');
          localStorage.removeItem('username');
          localStorage.removeItem('role');
          if (!window.location.pathname.includes('/login')) {
            window.location.replace('/login?reason=expired');
          }
        }
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
        localStorage.removeItem('role');
      }
    }

    return response;
  } catch (error) {
    console.error(`Error pada pemanggilan API fetch [${endpoint}]:`, error);
    throw error;
  }
};

// ─── Tipe Data User ───────────────────────────────────────────────────────────
export interface UserData {
  id: string;
  username: string;
  email: string;
  role: 'ADMIN' | 'ANALIS';
  is_active: boolean;
  dibuat_pada: string;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  role: 'ADMIN' | 'ANALIS';
}

// ─── API Manajemen User ───────────────────────────────────────────────────────

/** Ambil daftar semua pengguna dari backend */
export const fetchUsers = async (): Promise<UserData[]> => {
  const res = await apiFetch('/api/v1/users');
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal memuat daftar pengguna.');
  }
  return res.json();
};

/** Buat pengguna baru */
export const createUser = async (payload: CreateUserPayload): Promise<UserData> => {
  const res = await apiFetch('/api/v1/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal membuat pengguna baru.');
  }
  return res.json();
};

/** Hapus pengguna berdasarkan ID */
export const deleteUser = async (userId: string): Promise<void> => {
  const res = await apiFetch(`/api/v1/users/${userId}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal menghapus pengguna.');
  }
};

/** Update role atau status aktif pengguna */
export const updateUserStatus = async (
  userId: string,
  params: { is_active?: boolean; role?: string }
): Promise<UserData> => {
  const query = new URLSearchParams();
  if (params.is_active !== undefined) query.set('is_active', String(params.is_active));
  if (params.role !== undefined) query.set('role', params.role);

  const res = await apiFetch(`/api/v1/users/${userId}?${query.toString()}`, { method: 'PATCH' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal memperbarui pengguna.');
  }
  return res.json();
};

/** Ambil profil akun yang sedang login */
export const getMyProfile = async (): Promise<UserData> => {
  const res = await apiFetch('/api/v1/users/me');
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal mengambil profil.');
  }
  return res.json();
};

export interface UpdateProfilePayload {
  username?: string;
  email?: string;
  new_password?: string;
}

/** Update profil akun sendiri */
export const updateMyProfile = async (payload: UpdateProfilePayload): Promise<UserData> => {
  const res = await apiFetch('/api/v1/users/me', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal memperbarui profil.');
  }
  return res.json();
};

export interface KeluargaDetail {
  id_keluarga: string;
  nama_anggota_keluarga?: string;
  nik?: string;
  nomor_kartu_keluarga?: string;
  desil_nasional?: number;
  provinsi?: string;
  kode_provinsi?: string;
  kabupaten_kota?: string;
  kode_kabupaten_kota?: string;
  kecamatan?: string;
  kode_kecamatan?: string;
  kelurahan_desa?: string;
  kode_kelurahan_desa?: string;
  alamat?: string;
  jumlah_anggota_keluarga?: number;
  id_pelanggan_pln?: string;
  pbi_nas?: boolean;
  pbi_pemda?: boolean;
  status_kepemilikan_rumah?: string;
  luas_lantai?: number;
  jenis_lantai_terluas?: string;
  jenis_dinding_terluas?: string;
  jenis_atap_terluas?: string;
  sumber_air_minum_utama?: string;
  sumber_penerangan_utama?: string;
  daya_terpasang?: string;
  bahan_bakar_utama_memasak?: string;
  fasilitas_bab?: string;
  jenis_kloset?: string;
  pembuangan_akhir_tinja?: string;
  aset_bergerak_tabung_gas?: boolean;
  aset_bergerak_lemari_es?: boolean;
  aset_bergerak_ac?: boolean;
  aset_bergerak_pemanas_air?: boolean;
  aset_bergerak_tv_datar?: boolean;
  aset_bergerak_emas_perhiasan?: boolean;
  aset_bergerak_komputer_laptop_tablet?: boolean;
  aset_bergerak_sepeda_motor?: boolean;
  aset_bergerak_sepeda?: boolean;
  aset_bergerak_mobil?: boolean;
  aset_bergerak_perahu?: boolean;
  aset_bergerak_kapal_perahu_motor?: boolean;
  aset_bergerak_smartphone?: boolean;
  aset_bergerak_telepon_rumah?: boolean;
  aset_tidak_bergerak_lahan_lainnya?: boolean;
  aset_tidak_bergerak_rumah_lainnya?: boolean;
  jumlah_ternak_sapi?: number;
  jumlah_ternak_kerbau?: number;
  jumlah_ternak_kuda?: number;
  jumlah_ternak_babi?: number;
  jumlah_ternak_kambing_domba?: number;
}

/** Ambil detail keluarga dari database */
export const getKeluargaDetail = async (keluargaId: string): Promise<KeluargaDetail> => {
  const res = await apiFetch(`/api/v1/keluarga/${keluargaId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal mengambil detail keluarga.');
  }
  return res.json();
};
