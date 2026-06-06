import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "fs";

// Detect if running inside a Docker container to choose the correct backend host
const isDocker = fs.existsSync("/.dockerenv");
const target = isDocker ? "http://backend:8000" : "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: target,
        changeOrigin: true,
      },
      '/auth': {
        target: `${target}/api/v1/auth`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/auth/, '')
      },
    },
  },
});