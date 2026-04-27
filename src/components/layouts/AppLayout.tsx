import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { MobileNav } from "./MobileNav";

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <MobileNav />
        <main className="flex-1 overflow-y-auto bg-background/95 px-4 py-5 md:px-6 md:py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
        <footer className="hidden md:flex items-center justify-center border-t border-border px-6 py-2.5 text-[11px] text-muted-foreground shrink-0">
          <span>RD Design Copilot v1.1 · © 2026</span>
        </footer>
      </div>
    </div>
  );
}