import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ArtifactProvider } from "@/contexts/ArtifactContext";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layouts/AppLayout";
import { ErrorBoundary } from "@/components/ErrorBoundary";

// Critical path — eager
import Auth from "./pages/Auth";
import ResetPassword from "./pages/ResetPassword";
import ProjectList from "./pages/ProjectList";
import ProjectDashboard from "./pages/ProjectDashboard";
import NotFound from "./pages/NotFound";

// Non-critical — lazy loaded
const Settings = lazy(() => import("./pages/Settings"));
const TaskDefinition = lazy(() => import("./pages/TaskDefinition"));
const Track = lazy(() => import("./pages/Track"));
const Explore = lazy(() => import("./pages/Explore"));
const Create = lazy(() => import("./pages/Create"));
const PreCadReview = lazy(() => import("./pages/PreCadReview"));
const CadInProgress = lazy(() => import("./pages/CadInProgress"));
const DesignReview = lazy(() => import("./pages/DesignReview"));
const DecisionRecord = lazy(() => import("./pages/DecisionRecord"));
const Feynman = lazy(() => import("./pages/Feynman"));
const KnowledgeBase = lazy(() => import("./pages/KnowledgeBase"));
const ConstraintLabelDictionary = lazy(() => import("./pages/ConstraintLabelDictionary"));
const DevSeed = lazy(() => import("./pages/DevSeed"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 300_000,
      retry: (failureCount, error) => {
        // Never retry 4xx client errors (auth, validation, not-found, etc.)
        if (error && typeof error === "object" && "status" in error) {
          const status = (error as { status: number }).status;
          if (status >= 400 && status < 500) return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

const App = () => (
  <ErrorBoundary>
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <AuthProvider>
          <ArtifactProvider>
          <BrowserRouter>
            <Suspense fallback={<div className="flex h-screen w-full items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>}>
            <Routes>
              <Route path="/auth" element={<Auth />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/:id" element={<ProjectDashboard />} />
                <Route path="/projects/:id/brief" element={<TaskDefinition />} />
                <Route path="/projects/:id/explore" element={<Explore />} />
                <Route path="/projects/:id/track" element={<Track />} />
                <Route path="/projects/:id/create" element={<Create />} />
                <Route path="/projects/:id/pre-cad" element={<PreCadReview />} />
                <Route path="/projects/:id/cad" element={<CadInProgress />} />
                <Route path="/projects/:id/review" element={<DesignReview />} />
                <Route path="/projects/:id/decide" element={<DecisionRecord />} />
                <Route path="/projects/:id/feynman" element={<Feynman />} />
                <Route path="/projects/:id/constraint-labels" element={<ConstraintLabelDictionary />} />
                <Route path="/knowledge-base" element={<KnowledgeBase />} />
                <Route path="/knowledge-base/:slug" element={<KnowledgeBase />} />
                <Route path="/settings" element={<Settings />} />
                {import.meta.env.DEV && (
                  <Route path="/dev/seed" element={<DevSeed />} />
                )}
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
            </Suspense>
          </BrowserRouter>
          </ArtifactProvider>
        </AuthProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
