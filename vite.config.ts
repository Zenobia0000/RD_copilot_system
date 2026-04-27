import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "http://localhost:8000";
  const proxyTarget = apiBaseUrl.replace(/\/+$/, "").replace(/\/api\/v1$/i, "");

  return {
    server: {
      host: "::",
      port: 5173,
      strictPort: true,
      hmr: {
        overlay: false,
      },
      proxy: {
        "/api/v1": {
          target: proxyTarget || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
      dedupe: ["react", "react-dom", "react/jsx-runtime"],
    },
    optimizeDeps: {
      include: ["react", "react-dom", "react/jsx-runtime", "@tanstack/react-query"],
    },
    build: {
      target: "es2020",
      sourcemap: mode !== "production",
      cssCodeSplit: true,
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            if (!id.includes("node_modules")) return undefined;
            if (id.includes("react-dom") || id.includes("/react/") || id.includes("react-router")) {
              return "vendor-react";
            }
            if (id.includes("@radix-ui")) return "vendor-radix";
            if (id.includes("recharts") || id.includes("d3-")) return "vendor-charts";
            if (id.includes("@tanstack")) return "vendor-query";
            if (id.includes("@supabase")) return "vendor-supabase";
            if (id.includes("lucide-react")) return "vendor-icons";
            if (id.includes("date-fns") || id.includes("react-day-picker")) return "vendor-dates";
            return "vendor";
          },
        },
      },
    },
  };
});
