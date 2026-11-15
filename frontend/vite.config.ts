import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const proxyConfig = {
  '/v1': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
  '/health': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: proxyConfig,
  },
  preview: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: proxyConfig,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
