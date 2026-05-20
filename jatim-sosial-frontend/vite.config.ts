import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,      // Mengizinkan koneksi dari luar kontainer
    port: 5173,      // Port standar Vite
    watch: {
      usePolling: true, // Menggunakan polling untuk deteksi perubahan file di Windows host
    },
  },
});
