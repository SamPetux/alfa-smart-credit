import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const contractsDir = fileURLToPath(new URL("../contracts", import.meta.url));
const apiTarget = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Статусы и risk-v1 берутся только из contracts/, без копий во frontend.
    alias: { "@contracts": contractsDir },
  },
  server: {
    // Один origin в dev: cookie-сессия и CSRF работают так же, как за reverse proxy.
    proxy: { "/api": { target: apiTarget, changeOrigin: false } },
    fs: { allow: [".", contractsDir] },
  },
  build: { sourcemap: false, target: "es2022" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    restoreMocks: true,
  },
});
