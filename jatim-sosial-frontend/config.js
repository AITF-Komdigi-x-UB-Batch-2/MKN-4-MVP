// src/api.js
export const BASE_URL = "http://localhost:8000/api/v1";

// Fungsi bantuan untuk mengambil token dari local storage
export const getToken = () => localStorage.getItem("token_jatim");