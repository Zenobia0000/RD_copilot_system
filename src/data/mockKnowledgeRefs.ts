// Stub — mock data removed in WBS 4.3.4 refactor.
// TODO: Replace with useKnowledgeRefs hook once knowledge_refs DB table is created (Sprint 5+).
import type { KnowledgeRef } from "@/types/knowledge";

export const mockStepKnowledgeRefs: Record<number, KnowledgeRef[]> = {};
export const mockPageKnowledgeRefs: Record<string, KnowledgeRef[]> = {};
