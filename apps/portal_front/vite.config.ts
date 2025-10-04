import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const APP_VERSION = (globalThis as any)?.process?.env?.APP_VERSION || Date.now().toString();

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(APP_VERSION),
    // 환경변수 설정
    'import.meta.env.VITE_BILLING_ENABLED': JSON.stringify(process.env.VITE_BILLING_ENABLED || 'false'),
    'import.meta.env.VITE_PAID_READY': JSON.stringify(process.env.VITE_PAID_READY || 'false'),
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8006'),
  },
  server: {
    host: '0.0.0.0',
    port: 5172,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        secure: false
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 5172
  }
});
