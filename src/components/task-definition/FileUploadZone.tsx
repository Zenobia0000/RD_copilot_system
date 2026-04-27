import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Upload, File, X, FileText, Image, Sheet, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "uploading" | "done" | "error";
  progress: number;
  errorMessage?: string;
}

interface FileUploadZoneProps {
  files: UploadedFile[];
  onFilesChange: (files: UploadedFile[]) => void;
  onExtract: () => void;
  isExtracting: boolean;
}

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const MAX_SIZE = 20 * 1024 * 1024; // 20MB

function getFileIcon(type: string) {
  if (type.startsWith("image/")) return Image;
  if (type.includes("spreadsheet") || type.includes("excel") || type.includes("csv")) return Sheet;
  return FileText;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUploadZone({ files, onFilesChange, onExtract, isExtracting }: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const progressTimers = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  /** Simulate upload progress for a single file, then mark it done.
   *  TODO: Replace this simulation with a real upload call, e.g.:
   *    const res = await fetch("/api/upload", { method: "POST", body: formData });
   *  The progress callback should drive `onFilesChange` updates.
   */
  const simulateUploadProgress = useCallback((
    fileId: string,
    currentFiles: UploadedFile[],
    onUpdate: (files: UploadedFile[]) => void,
  ) => {
    let progress = 0;
    const timer = setInterval(() => {
      progress = Math.min(progress + 20 + Math.floor(Math.random() * 15), 100);
      const updated = currentFiles.map((f) =>
        f.id === fileId
          ? { ...f, progress, status: (progress >= 100 ? "done" : "uploading") as UploadedFile["status"] }
          : f,
      );
      onUpdate(updated);
      // Keep a mutable ref to latest files for subsequent ticks
      currentFiles = updated;
      if (progress >= 100) {
        clearInterval(timer);
        progressTimers.current.delete(fileId);
      }
    }, 200);
    progressTimers.current.set(fileId, timer);
  }, []);

  const processFiles = useCallback((fileList: FileList) => {
    const incoming: UploadedFile[] = [];
    const errors: string[] = [];

    Array.from(fileList).forEach((f) => {
      const isValidType = ACCEPTED_TYPES.some((t) => f.type === t) || f.name.endsWith(".pdf") || f.name.endsWith(".xlsx") || f.name.endsWith(".csv");
      const isValidSize = f.size <= MAX_SIZE;

      if (!isValidType) {
        errors.push(`${f.name}: 不支援的檔案格式`);
        incoming.push({ id: `f-${Date.now()}-${Math.random()}`, name: f.name, size: f.size, type: f.type, status: "error" as const, progress: 0, errorMessage: "不支援的檔案格式" });
        return;
      }
      if (!isValidSize) {
        toast.error(`檔案「${f.name}」超過 20 MB 限制`, { description: `實際大小：${formatSize(f.size)}` });
        incoming.push({ id: `f-${Date.now()}-${Math.random()}`, name: f.name, size: f.size, type: f.type, status: "error" as const, progress: 0, errorMessage: "檔案超過 20MB 限制" });
        return;
      }

      // TODO: Replace with real upload via backend endpoint.
      // File passes validation — start in "uploading" state with 0 progress.
      incoming.push({ id: `f-${Date.now()}-${Math.random()}`, name: f.name, size: f.size, type: f.type, status: "uploading" as const, progress: 0 });
    });

    const merged = [...files, ...incoming];
    onFilesChange(merged);

    // Kick off simulated progress for each valid (uploading) file
    incoming
      .filter((f) => f.status === "uploading")
      .forEach((f) => simulateUploadProgress(f.id, merged, onFilesChange));
  }, [files, onFilesChange, simulateUploadProgress]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) processFiles(e.target.files);
    e.target.value = "";
  };

  const removeFile = (id: string) => {
    onFilesChange(files.filter((f) => f.id !== id));
  };

  const doneFiles = files.filter((f) => f.status === "done");

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">多模態素材上傳</CardTitle>
        <p className="text-xs text-muted-foreground">支援 PDF、圖片 (JPG/PNG)、Excel (XLSX)、規格書，最大 20MB/檔案</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Dropzone */}
        <label
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={cn(
            "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 cursor-pointer transition-colors",
            isDragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
          )}
        >
          <Upload className="h-8 w-8 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">拖放檔案至此處，或點擊選擇</span>
          <input type="file" className="hidden" multiple accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.csv" onChange={handleInputChange} />
        </label>

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((f) => {
              const Icon = getFileIcon(f.type);
              return (
                <div key={f.id} className="flex items-center gap-3 rounded-md border p-2.5 text-sm">
                  <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{f.name}</span>
                      <span className="text-xs text-muted-foreground shrink-0">{formatSize(f.size)}</span>
                    </div>
                    {f.status === "uploading" && <Progress value={f.progress} className="h-1 mt-1" />}
                    {f.status === "error" && <p className="text-xs text-destructive mt-0.5">{f.errorMessage}</p>}
                  </div>
                  <Badge variant={f.status === "done" ? "default" : f.status === "error" ? "destructive" : "secondary"} className="text-[10px] shrink-0">
                    {f.status === "done" ? "完成" : f.status === "uploading" ? "上傳中" : "失敗"}
                  </Badge>
                  <button onClick={() => removeFile(f.id)} className="text-muted-foreground hover:text-destructive transition-colors shrink-0">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Extract button */}
        <Button onClick={onExtract} disabled={doneFiles.length === 0 || isExtracting} className="w-full sm:w-auto">
          {isExtracting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
          {isExtracting ? "AI 提取中..." : "開始 AI 提取"}
        </Button>
      </CardContent>
    </Card>
  );
}
