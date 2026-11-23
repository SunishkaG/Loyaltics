import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /api/* to FastAPI so the browser never hits CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: p => p.replace(/^\/api/, "") },
    },
  },
});
