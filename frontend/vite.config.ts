import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The FastAPI backend runs separately on 127.0.0.1:8000 (see backend/README.md).
// The dev server proxies API paths, so the browser stays same-origin and the app
// also works when the dev server is opened from a phone on the local network.
const apiTarget = process.env.FIELDSHIFT_API_TARGET ?? "http://127.0.0.1:8000";
const proxy = {
  "/api": { target: apiTarget, changeOrigin: false },
  "/health": { target: apiTarget, changeOrigin: false },
};

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy },
  preview: { port: 4173, strictPort: true, proxy },
  // three.js and Leaflet are loaded through dynamic imports, so they land in their own chunks.
  build: { target: "es2022", chunkSizeWarningLimit: 900 },
});
