import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

/** If auth loading exceeds this duration, treat it as a failure and redirect. */
const AUTH_LOADING_TIMEOUT_MS = 10_000;

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, session, isLoading } = useAuth();
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    if (!isLoading) return;

    const id = setTimeout(() => setTimedOut(true), AUTH_LOADING_TIMEOUT_MS);
    return () => clearTimeout(id);
  }, [isLoading]);

  // Still loading and within timeout — show skeleton
  if (isLoading && !timedOut) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="space-y-4 w-64 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4 mx-auto" />
        </div>
      </div>
    );
  }

  // No valid session or user (covers: timeout, auth error, session expiry)
  if (!user || !session) {
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
}
