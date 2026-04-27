import { useMemo, useCallback } from "react";
import { NavLink, useLocation, useParams, useNavigate } from "react-router-dom";
import logoImg from "@/assets/logo-delta.svg";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/components/ThemeProvider";
import { useProject } from "@/hooks/api/useProjects";
import {
  globalNavItems,
  projectSteps,
  phaseLabels,
  getStepStatus,
} from "@/config/navigationSteps";
import type { StepStatusValue } from "@/config/navigationSteps";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  LayoutDashboard,
  LogOut, Sun, Moon, Monitor, ChevronDown, Settings,
} from "lucide-react";

function StatusDot({ status }: { status: StepStatusValue }) {
  if (status === "completed") return <span className="text-[10px] text-primary">·</span>;
  if (status === "active") return <span className="text-[10px] animate-pulse text-primary">●</span>;
  return <span className="text-[10px] text-muted-foreground">○</span>;
}

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id: projectId } = useParams();
  const { user, signOut } = useAuth();
  const { theme, setTheme } = useTheme();

  const isInsideProject = !!projectId && location.pathname.startsWith(`/projects/${projectId}`);
  const { data: project } = useProject(isInsideProject ? projectId : undefined);

  const stepsByPhase = useMemo(
    () =>
      [1, 2, 3].map((phase) => ({
        phase,
        steps: projectSteps.filter((s) => s.phase === phase),
      })),
    [],
  );

  const initials = useMemo(
    () =>
      user?.user_metadata?.display_name
        ? user.user_metadata.display_name.slice(0, 2).toUpperCase()
        : user?.email?.slice(0, 2).toUpperCase() ?? "U",
    [user?.user_metadata?.display_name, user?.email],
  );

  const handleSignOut = useCallback(async () => {
    await signOut();
    navigate("/auth");
  }, [signOut, navigate]);

  const ThemeIcon = useMemo(
    () => (theme === "dark" ? Moon : theme === "light" ? Sun : Monitor),
    [theme],
  );

  return (
    <aside className="hidden md:flex md:flex-col md:w-60 border-r border-sidebar-border bg-sidebar shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-sidebar-border">
        <img src={logoImg} alt="RD Design Copilot" width={32} height={32} decoding="async" className="h-8 w-8 rounded-lg" />
        <span className="font-semibold text-sm text-sidebar-foreground tracking-tight">
          RD Design Copilot
        </span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {/* Global nav */}
        {globalNavItems.map((item) => {
          const isActive =
            location.pathname === item.path ||
            location.pathname.startsWith(item.path + "/");

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}

        {/* Project-context 6+1 navigation */}
        {isInsideProject && (
          <>
            <div className="pt-4 pb-1 px-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                專案流程
              </p>
            </div>

            {/* Dashboard link */}
            <NavLink
              to={`/projects/${projectId}`}
              end
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                location.pathname === `/projects/${projectId}`
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </NavLink>

            {/* 6+1 steps with phase grouping */}
            {stepsByPhase.map(({ phase, steps }) => (
              <div key={phase} className="space-y-0.5">
                <p className={cn("text-[10px] font-semibold px-3 pt-3 pb-0.5 uppercase tracking-wider",
                  phase === 1 ? "text-phase-1" : phase === 2 ? "text-phase-2" : "text-phase-3"
                )}>
                  Phase {phase} · {phaseLabels[phase]}
                </p>
                {steps.map(step => {
                  const status = getStepStatus(location.pathname, step.route, projectId!, project?.phase_progress);
                  const isActive = status === "active";
                  return (
                    <NavLink
                      key={step.id}
                      to={`/projects/${projectId}/${step.route}`}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-all duration-150 border-l-2 ml-1",
                        isActive
                          ? cn(
                              "bg-primary/5 text-primary font-medium",
                              phase === 1 ? "border-l-phase-1" : phase === 2 ? "border-l-phase-2" : "border-l-phase-3"
                            )
                          : "border-l-transparent text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <StatusDot status={status} />
                      <step.icon className="h-3.5 w-3.5" />
                      <span className="text-xs">{step.label}</span>
                      <span className="text-[10px] text-muted-foreground ml-auto">{step.zhLabel}</span>
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </>
        )}
      </nav>

      {/* User footer */}
      <div className="border-t border-sidebar-border p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2.5 w-full rounded-lg px-2 py-2 text-sm hover:bg-sidebar-accent transition-colors text-left">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-[10px] bg-primary text-primary-foreground font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate text-sidebar-foreground">
                  {user?.user_metadata?.display_name || user?.email || "使用者"}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">
                  {user?.email}
                </p>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuItem onClick={() => navigate("/settings")}>
              <Settings className="h-3.5 w-3.5 mr-2" /> 設定
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "dark" : "light")}>
              <ThemeIcon className="h-3.5 w-3.5 mr-2" />
              {theme === "dark" ? "切換至淺色" : theme === "light" ? "切換至深色" : "切換至淺色"}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} className="text-destructive focus:text-destructive">
              <LogOut className="h-3.5 w-3.5 mr-2" /> 登出
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}