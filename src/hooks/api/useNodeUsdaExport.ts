/**
 * useNodeUsdaExport — React Query mutation hook for generating a per-node
 * USD ASCII (.usda) file via the LLM-based endpoint.
 *
 * On success the hook automatically triggers a browser download of the
 * generated `.usda` file via a temporary Blob URL.
 */

import { useMutation } from "@tanstack/react-query";
import {
  exportUsdaLlm,
  type NodeUsdaLlmRequest,
  type UsdaExportResponse,
} from "@/lib/api";

// ── Variables accepted by the mutation ──────────────────────────────────────

export type NodeUsdaExportVariables = NodeUsdaLlmRequest;

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
 * Calls `POST /api/v1/export/usda-llm` with per-node context assembled
 * from the SpecTreeNode, then downloads the resulting `.usda` file.
 *
 * @example
 * ```tsx
 * const { mutate: generate, isPending } = useNodeUsdaExport();
 * generate({ node_name: "Motor", node_level: "component", ... });
 * ```
 */
export function useNodeUsdaExport() {
  return useMutation<UsdaExportResponse, Error, NodeUsdaExportVariables>({
    mutationFn: (vars) => exportUsdaLlm(vars),
    onSuccess: (data) => {
      downloadBlob(data.content, data.filename);
    },
  });
}
