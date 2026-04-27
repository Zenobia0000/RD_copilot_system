/**
 * ProjectDataContext — WBS 3.5.1/3.5.2
 * Unified context for cross-step data sharing.
 * Replaces per-page mock data imports with a central store.
 */
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import type { SocraticQuestion, ExploreContradiction, CausalLoop } from '@/types/explore';
import type { TrackAssumption, UnknownFactor } from '@/types/track';
import type { Alternative } from '@/types/create';

interface ProjectData {
  projectId: string;
  questions: SocraticQuestion[];
  contradictions: ExploreContradiction[];
  causalLoop: CausalLoop | null;
  assumptions: TrackAssumption[];
  unknownFactors: UnknownFactor[];
  alternatives: Alternative[];
  setQuestions: (q: SocraticQuestion[]) => void;
  setContradictions: (c: ExploreContradiction[]) => void;
  setCausalLoop: (cl: CausalLoop | null) => void;
  setAssumptions: (a: TrackAssumption[]) => void;
  setUnknownFactors: (f: UnknownFactor[]) => void;
  setAlternatives: (a: Alternative[]) => void;
}

const ProjectDataContext = createContext<ProjectData | null>(null);

export function ProjectDataProvider({ projectId, children }: { projectId: string; children: ReactNode }) {
  const [questions, setQuestions] = useState<SocraticQuestion[]>([]);
  const [contradictions, setContradictions] = useState<ExploreContradiction[]>([]);
  const [causalLoop, setCausalLoop] = useState<CausalLoop | null>(null);
  const [assumptions, setAssumptions] = useState<TrackAssumption[]>([]);
  const [unknownFactors, setUnknownFactors] = useState<UnknownFactor[]>([]);
  const [alternatives, setAlternatives] = useState<Alternative[]>([]);

  const value = useMemo<ProjectData>(
    () => ({
      projectId,
      questions, contradictions, causalLoop,
      assumptions, unknownFactors, alternatives,
      setQuestions, setContradictions, setCausalLoop,
      setAssumptions, setUnknownFactors, setAlternatives,
    }),
    [projectId, questions, contradictions, causalLoop, assumptions, unknownFactors, alternatives],
  );

  return (
    <ProjectDataContext.Provider value={value}>
      {children}
    </ProjectDataContext.Provider>
  );
}

export function useProjectData() {
  const ctx = useContext(ProjectDataContext);
  if (!ctx) throw new Error('useProjectData must be used within ProjectDataProvider');
  return ctx;
}
