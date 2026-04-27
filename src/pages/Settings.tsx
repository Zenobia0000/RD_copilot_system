import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/integrations/supabase/client";
import { useTheme } from "@/components/ThemeProvider";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { User, Mail, Sun, Moon, Monitor, Loader2, Lock } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Password change
  const [newPassword, setNewPassword] = useState("");
  const [changingPw, setChangingPw] = useState(false);

  useEffect(() => {
    if (!user) return;
    supabase
      .from("profiles")
      .select("display_name")
      .eq("user_id", user.id)
      .single()
      .then(({ data }) => {
        if (data) setDisplayName(data.display_name || "");
        setLoadingProfile(false);
      });
  }, [user]);

  const handleSaveProfile = async () => {
    if (!user) return;
    setSaving(true);
    const { error } = await supabase
      .from("profiles")
      .update({ display_name: displayName.trim() })
      .eq("user_id", user.id);
    setSaving(false);
    if (error) {
      toast.error("儲存失敗: " + error.message);
    } else {
      toast.success("已更新顯示名稱");
    }
  };

  const handleChangePassword = async () => {
    if (newPassword.length < 6) {
      toast.error("密碼至少 6 個字元");
      return;
    }
    setChangingPw(true);
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    setChangingPw(false);
    if (error) {
      toast.error("密碼更新失敗: " + error.message);
    } else {
      toast.success("密碼已更新");
      setNewPassword("");
    }
  };

  const themeOptions: { value: "light" | "dark" | "system"; label: string; icon: typeof Sun }[] = [
    { value: "light", label: "淺色", icon: Sun },
    { value: "dark", label: "深色", icon: Moon },
    { value: "system", label: "跟隨系統", icon: Monitor },
  ];

  return (
    <div className="page-shell-narrow max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">設定</h1>
        <p className="text-sm text-muted-foreground mt-1">管理您的帳號資訊與系統偏好</p>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <User className="h-4 w-4" /> 個人資料
          </CardTitle>
          <CardDescription>更新您的顯示名稱與帳號資訊</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Email</Label>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{user?.email ?? "—"}</span>
              <Badge variant="outline" className="text-[10px]">唯讀</Badge>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="displayName">顯示名稱</Label>
            <Input
              id="displayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="您的名稱"
              disabled={loadingProfile}
            />
          </div>
          <Button onClick={handleSaveProfile} disabled={saving || loadingProfile} size="sm">
            {saving && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
            儲存
          </Button>
        </CardContent>
      </Card>

      {/* Password */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Lock className="h-4 w-4" /> 變更密碼
          </CardTitle>
          <CardDescription>設定新的登入密碼</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="newPassword">新密碼</Label>
            <Input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="至少 6 個字元"
              minLength={6}
            />
          </div>
          <Button onClick={handleChangePassword} disabled={changingPw || newPassword.length < 6} size="sm">
            {changingPw && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
            更新密碼
          </Button>
        </CardContent>
      </Card>

      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sun className="h-4 w-4" /> 外觀主題
          </CardTitle>
          <CardDescription>選擇系統的顯示風格</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            {themeOptions.map((opt) => {
              const isActive = theme === opt.value;
              return (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                    isActive
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground/30"
                  }`}
                >
                  <opt.icon className={`h-6 w-6 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                  <span className={`text-sm font-medium ${isActive ? "text-primary" : "text-muted-foreground"}`}>
                    {opt.label}
                  </span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Separator />

      <div className="text-[11px] text-muted-foreground text-center pb-6">
        RD Design Copilot v1.1 · © 2026
      </div>
    </div>
  );
}
