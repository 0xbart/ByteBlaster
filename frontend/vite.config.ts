import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
const wsBackendUrl = backendUrl.replace(/^http/, "ws");

/**
 * Forward the real client IP to the backend. Without this, every browser
 * hitting the Vite dev server is seen by the backend as the Vite container's
 * IP, which breaks the IP-based auth (everyone "shares" the same user).
 *
 * Mirrors the prod nginx's `proxy_set_header X-Forwarded-For $remote_addr`.
 */
function setForwardedFor(proxyReq: { setHeader: (k: string, v: string) => void }, req: { socket?: { remoteAddress?: string | null }; headers?: Record<string, string | string[] | undefined> }): void {
  const raw = req.socket?.remoteAddress ?? "";
  // Strip the IPv4-mapped IPv6 prefix (::ffff:1.2.3.4 → 1.2.3.4).
  const ip = raw.replace(/^::ffff:/, "");
  if (ip) proxyReq.setHeader("X-Forwarded-For", ip);
}

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: backendUrl,
        changeOrigin: false,
        configure: (proxy) => {
          proxy.on("proxyReq", setForwardedFor);
        },
      },
      "/ws": {
        target: wsBackendUrl,
        ws: true,
        changeOrigin: false,
        configure: (proxy) => {
          proxy.on("proxyReqWs", setForwardedFor);
        },
      },
    },
  },
});
