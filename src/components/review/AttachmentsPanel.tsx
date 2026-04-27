import { useState, useRef, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Upload, FileText, Trash2, Loader2, Paperclip, X, ExternalLink, Copy } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

interface PendingFile {
  file: File;
  description: string;
}

interface Attachment {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  content_type: string | null;
  description: string;
  assumption_code: string | null;
  created_at: string;
}

interface AttachmentsPanelProps {
  projectId: string;
  attachments: Attachment[];
  onRefresh: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentsPanel({ projectId, attachments, onRefresh }: AttachmentsPanelProps) {
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) return;

    const maxSize = 20 * 1024 * 1024; // 20MB
    const tooLarge = files.filter(f => f.size > maxSize);
    if (tooLarge.length > 0) {
      toast.error(`${tooLarge.map(f => f.name).join(", ")} 超過 20MB 上限`);
    }

    const valid = files.filter(f => f.size <= maxSize);
    setPendingFiles(prev => [
      ...prev,
      ...valid.map(f => ({ file: f, description: "" })),
    ]);

    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const updateDescription = (index: number, desc: string) => {
    setPendingFiles(prev => prev.map((p, i) => i === index ? { ...p, description: desc } : p));
  };

  const removePending = (index: number) => {
    setPendingFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUploadAll = async () => {
    if (pendingFiles.length === 0) return;

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      toast.error("請先登入");
      return;
    }

    setUploading(true);
    let successCount = 0;

    for (const pf of pendingFiles) {
      const ext = pf.file.name.split(".").pop() ?? "";
      const filePath = `${user.id}/${projectId}/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.${ext}`;

      const { error: uploadError } = await supabase.storage
        .from("review-attachments")
        .upload(filePath, pf.file, { contentType: pf.file.type });

      if (uploadError) {
        toast.error(`上傳 ${pf.file.name} 失敗: ${uploadError.message}`);
        continue;
      }

      const { error: dbError } = await supabase
        .from("review_attachments")
        .insert({
          project_id: projectId,
          user_id: user.id,
          file_name: pf.file.name,
          file_path: filePath,
          file_size: pf.file.size,
          content_type: pf.file.type || null,
          description: pf.description.trim(),
        });

      if (dbError) {
        toast.error(`記錄 ${pf.file.name} 失敗: ${dbError.message}`);
        continue;
      }

      successCount++;
    }

    setUploading(false);
    setPendingFiles([]);
    if (successCount > 0) {
      toast.success(`已上傳 ${successCount} 份文件`);
      onRefresh();
    }
  };

  const handleDelete = async (att: Attachment) => {
    setDeleting(att.id);

    const { error: storageError } = await supabase.storage
      .from("review-attachments")
      .remove([att.file_path]);

    if (storageError) {
      toast.error(`刪除檔案失敗: ${storageError.message}`);
      setDeleting(null);
      return;
    }

    const { error: dbError } = await supabase
      .from("review_attachments")
      .delete()
      .eq("id", att.id);

    if (dbError) {
      toast.error(`刪除記錄失敗: ${dbError.message}`);
    } else {
      toast.success("已刪除");
      onRefresh();
    }
    setDeleting(null);
  };

  const getPublicUrl = (filePath: string) => {
    const { data } = supabase.storage.from("review-attachments").getPublicUrl(filePath);
    return data.publicUrl;
  };

  const handleCopyLink = (filePath: string) => {
    const url = getPublicUrl(filePath);
    navigator.clipboard.writeText(url).then(() => {
      toast.success("已複製檔案連結");
    }).catch(() => {
      toast.error("複製失敗，請手動複製");
    });
  };

  return (
    <div className="space-y-4">
      {/* Existing attachments */}
      {attachments.length > 0 && (
        <div className="space-y-3">
          {attachments.map((att) => (
            <Card key={att.id} className="bg-muted/20">
              <CardContent className="p-4 flex items-start gap-3">
                <FileText className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <a
                      href={getPublicUrl(att.file_path)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium hover:underline text-primary flex items-center gap-1 truncate"
                    >
                      {att.file_name}
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                    <Badge variant="outline" className="text-[9px] shrink-0">
                      {formatFileSize(att.file_size)}
                    </Badge>
                    {att.assumption_code && (
                      <Badge variant="secondary" className="text-[9px]">{att.assumption_code}</Badge>
                    )}
                  </div>
                  {att.description && (
                    <p className="text-xs text-muted-foreground leading-relaxed">{att.description}</p>
                  )}
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(att.created_at).toLocaleString("zh-TW")}
                  </p>
                </div>
                <div className="flex gap-1 shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-primary"
                    onClick={() => handleCopyLink(att.file_path)}
                    title="複製檔案連結"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                    onClick={() => handleDelete(att)}
                    disabled={deleting === att.id}
                  >
                    {deleting === att.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pending files staging area */}
      {pendingFiles.length > 0 && (
        <div className="space-y-3 border border-dashed rounded-lg p-4">
          <p className="text-xs font-medium text-muted-foreground">待上傳文件 ({pendingFiles.length})</p>
          {pendingFiles.map((pf, i) => (
            <div key={i} className="flex items-start gap-3 bg-muted/30 rounded-lg p-3">
              <Paperclip className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">{pf.file.name}</span>
                  <Badge variant="outline" className="text-[9px] shrink-0">{formatFileSize(pf.file.size)}</Badge>
                </div>
                <Textarea
                  value={pf.description}
                  onChange={(e) => updateDescription(i, e.target.value)}
                  placeholder="文件概略描述（選填）：例如「ANSYS 熱仿真報告，驗證散熱片面積假設」"
                  rows={2}
                  maxLength={300}
                  className="text-xs"
                />
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={() => removePending(i)}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
          <Button onClick={handleUploadAll} disabled={uploading} size="sm">
            {uploading ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Upload className="h-3.5 w-3.5 mr-1.5" />}
            上傳全部 ({pendingFiles.length} 份)
          </Button>
        </div>
      )}

      {/* Upload trigger */}
      <div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.webp,.step,.iges,.stl,.stp,.csv,.txt"
        />
        <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
          <Paperclip className="h-3.5 w-3.5 mr-1.5" /> 選擇文件
        </Button>
        <p className="text-[10px] text-muted-foreground mt-1.5">
          支援 PDF、Office、圖片、CAD 檔案等，單檔上限 20MB，可多選
        </p>
      </div>
    </div>
  );
}
