import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useCreateProject } from "@/hooks/api/useProjects";

interface CreateProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectModal({ open, onOpenChange }: CreateProjectModalProps) {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

  const createProject = useCreateProject();

  function validate() {
    const e: typeof errors = {};
    if (!name || name.length < 2) e.name = "專案名稱至少需要 2 個字元";
    if (name.length > 100) e.name = "專案名稱不可超過 100 字元";
    if (!description || description.length < 10) e.description = "需求描述至少需要 10 個字元";
    if (description.length > 1000) e.description = "需求描述不可超過 1000 字元";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit() {
    if (!validate()) return;

    createProject.mutate(
      { name, description },
      {
        onSuccess: (project) => {
          onOpenChange(false);
          setName("");
          setDescription("");
          navigate(`/projects/${project.id}`);
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>新增專案</DialogTitle>
          <DialogDescription>填寫專案基本資訊以建立新的概念設計專案。</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="project-name">
              專案名稱 <span className="text-destructive">*</span>
            </Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例：E-Bike 動力傳動系統設計"
              maxLength={100}
            />
            {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="project-desc">
              需求描述 <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="project-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="描述專案的目標、範圍與關鍵需求..."
              maxLength={1000}
              rows={4}
            />
            {errors.description && <p className="text-xs text-destructive">{errors.description}</p>}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSubmit} disabled={createProject.isPending}>
            {createProject.isPending ? "建立中..." : "建立專案"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
