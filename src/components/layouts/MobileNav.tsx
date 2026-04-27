import { useState, useMemo, useCallback } from "react";
import logoImg from "@/assets/logo-delta.svg";
import { NavLink, useLocation, useParams, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/components/ThemeProvider";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  globalNavItems,
  projectSteps,
  phaseLabels,
} from "@/config/navigationSteps";
import {
  LayoutDashboard, Menu,
  LogOut, Sun, Moon, Monitor,
} from "lucide-react";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { id: projectId } = useParams();
  const { user, signOut } = useAuth();
  const { theme, setTheme } = useTheme();

  const isInsideProject = !!projectId && location.pathname.startsWith(`/projects/${projectId}`);

  const initials = useMemo(
    () =>
      user?.user_metadata?.display_name
        ? user.user_metadata.display_name.slice(0, 2).toUpperCase()
        : user?.email?.slice(0, 2).toUpperCase() ?? "U",
    [user?.user_metadata?.display_name, user?.email],
  );

  const handleSignOut = useCallback(async () => {
    setOpen(false);
    await signOut();
    navigate("/auth");
  }, [signOut, navigate]);

  const ThemeIcon = useMemo(
    () => (theme === "dark" ? Moon : theme === "light" ? Sun : Monitor),
    [theme],
  );

  return (
    <header className="flex items-center justify-between border-b border-border px-4 py-3 md:hidden bg-card">
      <div className="flex items-center gap-2.5">
        <img src={logoImg} alt="RD Design Copilot" className="h-7 w-7 rounded-md" />
        <span className="font-semibold text-sm tracking-tight">RD Design Copilot</span>
      </div>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0 flex flex-col">
          <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border">
            <img src={logoImg} alt="RD Design Copilot" className="h-8 w-8 rounded-lg" />
            <span className="font-semibold text-sm tracking-tight">RD Design Copilot</span>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {globalNavItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                location.pathname.startsWith(item.path + "/");
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-foreground hover:bg-muted"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              );
            })}

            {isInsideProject && (
              <>
                <div className="pt-3 pb-1 px-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">專案流程</p>
                </div>
                <NavLink to={`/projects/${projectId}`} end onClick={() => setOpen(false)}
                  className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                    location.pathname === `/projects/${projectId}` ? "bg-primary/10 text-primary" : "text-foreground hover:bg-muted"
                  )}>
                  <LayoutDashboard className="h-4 w-4" /> Dashboard
                </NavLink>
                {[1, 2, 3].map(phase => (
                  <div key={phase}>
                    <p className={cn("text-[10px] font-semibold px-3 pt-3 pb-0.5 uppercase tracking-wider",
                      phase === 1 ? "text-phase-1" : phase === 2 ? "text-phase-2" : "text-phase-3"
                    )}>
                      Phase {phase} · {phaseLabels[phase]}
                    </p>
                    {projectSteps.filter(s => s.phase === phase).map(step => {
                      const fullPath = `/projects/${projectId}/${step.route}`;
                      const isActive = location.pathname === fullPath || location.pathname.startsWith(fullPath + "/");
                      return (
                        <NavLink key={step.id} to={fullPath} onClick={() => setOpen(false)}
                          className={cn("flex items-center gap-3 rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-150 ml-2",
                            isActive ? "bg-primary/10 text-primary" : "text-foreground hover:bg-muted"
                          )}>
                          <step.icon className="h-3.5 w-3.5" />
                          {step.label} <span className="text-muted-foreground ml-auto">{step.zhLabel}</span>
                        </NavLink>
                      );
                    })}
                  </div>
                ))}
              </>
            )}
          </nav>

          {/* User footer */}
          <div className="border-t border-border p-3 space-y-2">
            <div className="flex items-center gap-2.5 px-2">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-[10px] bg-primary text-primary-foreground font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{user?.user_metadata?.display_name || user?.email}</p>
              </div>
            </div>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" className="flex-1 text-xs justify-start"
                onClick={() => { setTheme(theme === "dark" ? "light" : "dark"); }}>
                <ThemeIcon className="h-3.5 w-3.5 mr-1.5" />
                {theme === "dark" ? "淺色" : "深色"}
              </Button>
              <Button variant="ghost" size="sm" className="flex-1 text-xs justify-start text-destructive hover:text-destructive"
                onClick={handleSignOut}>
                <LogOut className="h-3.5 w-3.5 mr-1.5" /> 登出
              </Button>
            </div>
            <p className="text-[10px] text-muted-foreground text-center pt-1">v1.1 · © 2026</p>
          </div>
        </SheetContent>
      </Sheet>
    </header>
  );
}