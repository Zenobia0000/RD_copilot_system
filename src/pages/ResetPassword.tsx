import { useState, useEffect } from "react";
import logoImg from "@/assets/logo-delta.svg";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, Lock } from "lucide-react";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecovery, setIsRecovery] = useState(false);

  useEffect(() => {
    // Check for recovery event from URL hash
    const hash = window.location.hash;
    if (hash.includes("type=recovery")) {
      setIsRecovery(true);
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        setIsRecovery(true);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error("密碼至少 6 個字元");
      return;
    }
    setIsLoading(true);
    const { error } = await supabase.auth.updateUser({ password });
    setIsLoading(false);
    if (error) {
      toast.error(error.message);
    } else {
      toast.success("密碼已重設，將自動導向首頁");
      setTimeout(() => navigate("/projects"), 1500);
    }
  };

  if (!isRecovery) {
    return (
      <div className="auth-shell">
        <Card className="w-full max-w-sm">
          <CardContent className="p-6 text-center space-y-3">
            <p className="text-muted-foreground">無效的重設連結</p>
            <Button variant="outline" onClick={() => navigate("/auth")}>返回登入</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <img src={logoImg} alt="RD Design Copilot" className="h-12 w-12 rounded-2xl mx-auto shadow-card" />
          <h1 className="text-2xl font-bold tracking-tight">重設密碼</h1>
          <p className="text-sm text-muted-foreground">請輸入新的密碼</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <form onSubmit={handleReset} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">新密碼</label>
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
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                重設密碼
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
