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
  // Identitas individu (Kepala Keluarga)
  id: string;
  nama?: string;
  nik?: string;
  no_kk?: string;
  tempat_lahir?: string;
  tanggal_lahir?: string;
  umur_2026?: number;
  id_jenis_kelamin?: number;
  id_hub_kepala_keluarga?: number;
  id_status_perkawinan?: number;
  pbi?: number;
  status_dtsen?: string;

  // Pendidikan & Pekerjaan
  id_partisipasi_sekolah?: number;
  id_jenjang_pendidikan_dukcapil?: number;
  membantu_bekerja?: number;
  id_lapangan_usaha_dari_usaha_utama?: number;
  id_status_kedudukan_pekerjaan_utama?: number;
  id_kepemilikan_izin_usaha?: number;
  jumlah_jenis_usaha?: number;
  id_pekerjaan_utama?: number;
  jumlah_pekerja_dibayar?: number;
  jumlah_pekerja_tidak_dibayar?: number;
  id_omset_usaha_utama?: number;

  // Disabilitas & Kesehatan
  id_disabilitas?: number;
  tingkat_disabilitas?: string;
  id_kondisi_gizi?: number;
  id_penglihatan?: number;
  id_pendengaran?: number;
  id_berjalan_atau_naik_tangga?: number;
  id_menggunakan_tangan_jari?: number;
  id_belajar_kemampuan_intelektual?: number;
  id_pengendalian_perilaku?: number;
  id_berbicara_komunikasi?: number;
  id_mengurus_diri?: number;
  id_mengingat_berkonsentrasi?: number;
  id_kesedihan_depresi?: number;
  id_penyakit_menahun?: number;

  // Bansos flags
  kpm_jawara?: number;
  putri_jawara?: number;
  aspd?: number;
  ppks_jawara?: number;
  kemiskinan_ekstrem?: number;
  pkh_plus?: number;

  // Wilayah (Keluarga)
  desil_nasional_anggota?: number;
  desil_nasional_keluarga?: number;
  kode_kabupaten_kota?: string;
  kabupaten_kota?: string;
  kode_kecamatan?: string;
  kecamatan?: string;
  kode_kelurahan_desa?: string;
  kelurahan_desa?: string;
  alamat?: string;
  jumlah_anggota_keluarga?: number;
  desil_nasional?: number;

  // Bangunan
  id_status_penguasaan_bangunan?: number;
  id_lantai_terluas?: number;
  luas_lantai_bangunan?: number;
  id_dinding_terluas?: number;
  id_atap_terluas?: number;

  // Sanitasi & Air
  id_sumber_airminum?: number;
  id_fasilitas_bab?: number;
  id_jenis_kloset?: number;
  id_pembuangan_tinja?: number;

  // Energi
  id_sumberpenerangan?: number;
  id_dayapenerangan?: number;
  id_bb_utama?: number;

  // Aset bergerak (0/1)
  kepemilikan_aset?: number;
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
  lahan_tempat_lain?: number;
  rumah_tempat_lain?: number;

  // Ternak
  jml_sapi?: number;
  jml_kerbau?: number;
  jml_kuda?: number;
  jml_babi?: number;
  jml_kambing_domba?: number;
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
