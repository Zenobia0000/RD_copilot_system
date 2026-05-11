/**
 * useUsdaExport — React Query mutation hook for exporting the subsystem
 * hierarchy + engineering spec drafts as a USD ASCII (.usda) file.
 *
 * On success the hook automatically triggers a browser download of the
 * generated `.usda` file via a temporary Blob URL.
 */

import { useMutation } from "@tanstack/react-query";
import {
  exportUsda,
  type UsdaExportRequest,
  type UsdaExportResponse,
} from "@/lib/api";

// ── Variables accepted by the mutation ──────────────────────────────────────

export type UsdaExportVariables = UsdaExportRequest;

// ── Internal: trigger browser download ──────────────────────────────────────

function downloadBlob(content: string, filename: string): void {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  // Cleanup after a short delay so the browser can finish the download.
  setTimeout(() => {
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 100);
}

// ── Hook ────────────────────────────────────────────────────────────────────

/**
 * Calls `POST /api/v1/export/usda` with the subsystem tree, engineering
 * spec drafts and optional package map, then downloads the resulting
 * `.usda` file to the user's machine.
 *
 * @example
 * ```tsx
 * const { mutate: exportUsda, isPending } = useUsdaExport();
 * exportUsda({ project_id: id, subsystems, drafts, package_map });
 * ```
 */
export function useUsdaExport() {
  return useMutation<UsdaExportResponse, Error, UsdaExportVariables>({
    mutationFn: (vars) => exportUsda(vars),
    onSuccess: (data) => {
      downloadBlob(data.content, data.filename);
    },
  });
}
