export interface ReviewDimension {
  id: string;
  label: string;
  description: string;
  rating: "pass" | "concern" | "fail" | null;
  summary: string;
}

export interface SolutionReview {
  solutionId: string;
  dimensions: ReviewDimension[];
  reviewed: boolean;
}

export interface PreCadReviewState {
  reviews: SolutionReview[];
  selectedSolutionIds: string[];
  conclusion: string;
}
