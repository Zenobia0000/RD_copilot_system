import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { supabase } from "@/integrations/supabase/client";
import type { User, Session } from "@supabase/supabase-js";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  isLoading: true,
  signOut: async () => {},
});

// Double-guard: bypass only works in Vite dev server, never in production builds
const DEV_BYPASS_AUTH = import.meta.env.DEV && import.meta.env.VITE_DEV_BYPASS_AUTH === "true";

if (!import.meta.env.DEV && import.meta.env.VITE_DEV_BYPASS_AUTH === "true") {
  console.error("[Auth] CRITICAL: VITE_DEV_BYPASS_AUTH is enabled in a production build. Ignoring.");
}

const MOCK_USER = {
  id: "dev-admin-00000000",
  email: "admin@dev.local",
  user_metadata: { display_name: "Dev Admin" },
  app_metadata: { provider: "email", role: "admin" },
  aud: "authenticated",
  role: "authenticated",
  created_at: new Date().toISOString(),
} as unknown as User;

const MOCK_SESSION = {
  user: MOCK_USER,
  access_token: "dev-bypass-token",
  refresh_token: "dev-bypass-refresh",
  expires_in: 999999,
  token_type: "bearer",
} as unknown as Session;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(DEV_BYPASS_AUTH ? MOCK_USER : null);
  const [session, setSession] = useState<Session | null>(DEV_BYPASS_AUTH ? MOCK_SESSION : null);
  const [isLoading, setIsLoading] = useState(!DEV_BYPASS_AUTH);

  useEffect(() => {
    if (DEV_BYPASS_AUTH) {
      console.warn("[Auth] DEV BYPASS MODE — skipping Supabase auth");
      return;
    }

    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setIsLoading(false);
    });

    // THEN check initial session
    supabase.auth.getSession()
      .then(({ data: { session } }) => {
        setSession(session);
        setUser(session?.user ?? null);
      })
      .catch((err) => {
        console.error("[Auth] Failed to fetch session:", err);
        setSession(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, session, isLoading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
