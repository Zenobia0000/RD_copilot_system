/**
 * Runtime feature flags for the Create / Design Copilot app.
 *
 * Flags default to **off** and are enabled per-env via Vite `VITE_*`
 * environment variables so that production rolls out changes gradually.
 */

function readEnv(name: string): string | undefined {
  // `import.meta.env` may be undefined in certain ts-node contexts (tests);
  // guard both accesses.
  const env = (import.meta as unknown as { env?: Record<string, string | undefined> })
    .env;
  return env?.[name];
}

function readBool(name: string, defaultValue: boolean): boolean {
  const raw = readEnv(name);
  if (raw == null) return defaultValue;
  return raw === "true" || raw === "1" || raw === "on";
}

export const featureFlags = {
  /**
   * **TRIZ Directed Mode** (v8) — the Create Tab ① TRIZ convergence step
   * calls `POST /triz/solve-directed` (parallel TC/PC/SF → cluster → score →
   * Top1/Top2). This is the only supported mode since v8.
   *
   * The env-var override is kept for emergency kill-switch purposes only.
   */
  trizDirectedMode: readBool("VITE_TRIZ_DIRECTED_MODE", true),
} as const;

export type FeatureFlags = typeof featureFlags;
