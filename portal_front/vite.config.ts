import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "path";

const APP_VERSION =
  (globalThis as any)?.process?.env?.APP_VERSION || Date.now().toString();

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  define: {
    __APP_VERSION__: JSON.stringify(APP_VERSION),
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@/shared": path.resolve(__dirname, "../shared"),
      "@shared/editor": path.resolve(__dirname, "../shared/editor/src"),
      "@shared/schemas": path.resolve(__dirname, "../shared/schemas/src"),
      "@dreamseed/shared-editor": path.resolve(
        __dirname,
        "../shared/editor/src"
      ),
      "@dreamseed/shared-schemas": path.resolve(
        __dirname,
        "../shared/schemas/src"
      ),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8010",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5172,
  },
});
