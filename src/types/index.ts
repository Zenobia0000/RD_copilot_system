// Barrel export for all type modules.
// New code can use: import type { X } from '@/types'

// --- artifact.ts ---
export type {
  ArtifactState,
  ArtifactType,
  ArtifactMeta,
  ArtifactStateTransition,
  ConstraintArtifact,
  ContradictionArtifact,
  BreakpointArtifact,
  ConceptRouteArtifact,
  InterfaceContract as ArtifactInterfaceContract,
  EvidenceArtifact,
  RiskArtifact,
  CoreArtifact,
  AdverseConsequence as ArtifactAdverseConsequence,
} from './artifact';
export {
  ARTIFACT_STATE_ORDER,
  ARTIFACT_STATE_CONFIG,
  isValidTransition,
  ARTIFACT_TYPE_CONFIG,
  INTERFACE_CONTRACT_DIMENSIONS,
  EMPTY_INTERFACE_CONTRACT as ARTIFACT_EMPTY_INTERFACE_CONTRACT,
  GATE_ARTIFACT_TRANSITIONS,
  computeACLevel as artifactComputeACLevel,
} from './artifact';

// --- assumption.ts ---
export type {
  AssumptionStatus,
  VerificationStage,
  Assumption,
  AssumptionFormValues,
  CLDNode,
  CLDEdge,
  CLDLoop,
  LinkedContradiction,
  SocraticFeedback,
  ConvergenceImpact,
} from './assumption';
export {
  ASSUMPTION_STATUS_LABELS,
  VERIFICATION_STAGE_LABELS,
  VERIFICATION_METHODS,
  SEVERITY_LABELS,
  assumptionSchema,
} from './assumption';

// --- conceptRoute.ts ---
export type {
  AdoptionType,
  CompatibilityResult,
  SolutionCompatibility,
  CompositionEntry,
  ConceptRoute,
  CompatibilityMatrix,
  AntiPatternCheck,
  MultiSolutionAdoptionState,
} from './conceptRoute';
export { ADOPTION_TYPE_LABELS } from './conceptRoute';

// --- contradiction.ts ---
export type {
  TrizParameter,
  ContradictionSeverity,
  Contradiction,
  ContradictionFormData,
} from './contradiction';
export { CONTRADICTION_SEVERITIES, DEFAULT_SEVERITY } from './contradiction';

// --- convergence.ts ---
export type {
  ConvergenceStatus,
  BranchStatus,
  ExplorationSolution,
  ScanResultEntry,
  ExplorationRound,
  BranchExploration,
  MinorContradiction,
  ConvergenceState,
  ConvergenceLoopActions,
} from './convergence';

// --- create.ts ---
export type {
  AccordionStepStatus,
  CreateStepProgress,
  AntiAnchorRoute,
  TrizPath,
  TrizActionStatus,
  TrizSolution,
  SubsystemSource,
  Subsystem,
  InterfaceContract,
  AlternativeSource,
  Alternative,
  MustCriterion,
  CreateGateItem,
} from './create';
export {
  INTERFACE_CONTRACT_DIMS,
  EMPTY_INTERFACE_CONTRACT,
  DEFAULT_MUST_CRITERIA,
  MUST_CRITERIA,
  PRECAD_DIMENSIONS,
} from './create';

// --- decisionRecord.ts ---
export type {
  WantCriterion,
  WantScoreEvidence,
  WantScore,
  ACProbability,
  ACSeverity,
  ACLevel,
  AdverseConsequence,
  DecisionStatus,
  ActionItem,
  KtDecision,
  SignatureStatus,
  Signature,
  DecideGateItem,
} from './decisionRecord';
export { computeACLevel, DEFAULT_WANT_TEMPLATE } from './decisionRecord';

// --- designReview.ts ---
export type {
  EvidenceLevel,
  EvidenceMatrixRow,
  RiskItem,
  Experiment as DesignReviewExperiment,
  Gate31Item,
} from './designReview';
export {
  EVIDENCE_LEVELS,
  getRiskScore,
  getRiskLevel,
  getRiskColor,
  EXP_STATUS_COLOR,
} from './designReview';

// --- evidenceEntry.ts ---
export type { EvidenceEntry, KpiStatus } from './evidenceEntry';

// --- explore.ts ---
export type {
  QuestionCategory,
  SocraticQuestion,
  ContradictionType,
  ContradictionStatus,
  ExploreContradiction,
  CausalNode,
  CausalEdge,
  CausalLoop,
  GateCheckItem as ExploreGateCheckItem,
  GateCheckResult,
} from './explore';
export { CATEGORY_CONFIG } from './explore';

// --- knowledge.ts ---
export type { KnowledgeRef, KnowledgeArticle } from './knowledge';

// --- preCadReview.ts ---
export type {
  ReviewDimension,
  SolutionReview,
  PreCadReviewState,
} from './preCadReview';

// --- project.ts ---
export type {
  ProjectStatus,
  StepStatus,
  PhaseProgress,
  QuickStats,
  MustCriterionConfig,
  Project,
  CriticalKPI,
  ProjectHistoryItem,
  ProjectStage,
  NavCardDef,
  PreCadScore,
  ContradictionConvergence,
} from './project';
export { PROJECT_STATUS_LABELS } from './project';

// --- shared.ts ---
export type { ExperimentStatus, RiskLevel } from './shared';

// --- solution.ts ---
export type {
  MustCriteria,
  SolutionRisk,
  SecondaryContradiction,
  Solution,
  ConvergenceNode,
  ConvergenceEdge,
  HealthStatus,
} from './solution';

// --- taskDefinition.ts ---
export type {
  BriefConstraint,
  BriefKPI,
  TaskDefinition5W1H,
  GateCheckItem,
  BriefData,
  TaskDefinitionKPI,
  TaskDefinitionData,
  TaskDefinitionFormValues,
} from './taskDefinition';
export {
  briefValidationSchema,
  taskDefinitionSchema,
} from './taskDefinition';

// --- track.ts ---
export type {
  VerificationStatus,
  AssumptionSource,
  TrackAssumption,
  UnknownStatus,
  ImpactLevel,
  UnknownFactor,
  Experiment as TrackExperiment,
  TrackGateItem,
} from './track';
export {
  VERIFICATION_STATUS_CONFIG,
  RISK_LEVEL_CONFIG,
  KANBAN_COLUMNS,
  IMPACT_CONFIG,
  UNKNOWN_STATUS_CONFIG,
  EXPERIMENT_STATUS_CONFIG,
} from './track';
