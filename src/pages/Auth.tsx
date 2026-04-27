import { useState } from "react";
import logoImg from "@/assets/logo-delta.svg";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, Mail, Lock, User, ArrowLeft } from "lucide-react";

type AuthView = "login" | "signup" | "forgot";

export default function Auth() {
  const navigate = useNavigate();
  const [view, setView] = useState<AuthView>("login");
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (view === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        toast.success("登入成功");
        navigate("/projects");
      } else if (view === "signup") {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { display_name: displayName },
            emailRedirectTo: window.location.origin,
          },
        });
        if (error) throw error;
        toast.success("註冊成功！請檢查 Email 完成驗證。");
      } else if (view === "forgot") {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/reset-password`,
        });
        if (error) throw error;
        toast.success("重設連結已寄送至您的信箱");
      }
    } catch (error: any) {
      toast.error(error.message || "操作失敗");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center space-y-3">
          <img src={logoImg} alt="RD Design Copilot" width={56} height={56} decoding="async" className="h-14 w-14 rounded-2xl mx-auto shadow-card" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">RD Design Copilot</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {view === "login" ? "登入以繼續" : view === "signup" ? "建立帳號" : "重設密碼"}
            </p>
          </div>
        </div>

        <Card className="shadow-card-hover">
          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {view === "forgot" && (
                <button
                  type="button"
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
                  onClick={() => setView("login")}
                >
                  <ArrowLeft className="h-3 w-3" /> 返回登入
                </button>
              )}

              {view === "signup" && (
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">顯示名稱</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="你的名稱"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="pl-9"
                      required
                    />
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-9"
                    required
                  />
                </div>
              </div>

              {view !== "forgot" && (
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">密碼</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="password"
                      placeholder="至少 6 個字元"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-9"
                      minLength={6}
                      required
                    />
                  </div>
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {view === "login" ? "登入" : view === "signup" ? "註冊" : "寄送重設連結"}
              </Button>
            </form>

            <div className="mt-4 space-y-2 text-center">
              {view === "login" && (
                <>
                  <button
                    type="button"
                    className="text-sm text-muted-foreground hover:text-primary transition-colors block w-full"
                    onClick={() => setView("forgot")}
                  >
                    忘記密碼？
                  </button>
                  <button
                    type="button"
                    className="text-sm text-muted-foreground hover:text-primary transition-colors block w-full"
                    onClick={() => setView("signup")}
                  >
                    還沒有帳號？點此註冊
                  </button>
                </>
              )}
              {view === "signup" && (
                <button
                  type="button"
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  onClick={() => setView("login")}
                >
                  已有帳號？點此登入
                </button>
              )}
            </div>
          </CardContent>
        </Card>

        <p className="text-[11px] text-muted-foreground text-center">
          RD Design Copilot v1.1 · AI 輔助概念設計系統
        </p>
      </div>
    </div>
  );
}