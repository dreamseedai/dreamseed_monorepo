import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

const APP_VERSION = (globalThis as any)?.process?.env?.APP_VERSION || Date.now().toString();

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(APP_VERSION),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/shared': path.resolve(__dirname, '../shared'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5172,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
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
