import React, { Component, Suspense, type ReactNode, type ErrorInfo } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorFallback, type ErrorFallbackProps } from '@/components/ui/error-fallback';

// ---------------------------------------------------------------------------
// ErrorBoundary (internal)
// ---------------------------------------------------------------------------

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: React.ComponentType<ErrorFallbackProps>;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Minimal class-based ErrorBoundary.
 * Catches rendering errors in its children and delegates to a fallback component.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[QueryBoundary] Caught error:', error, info);
  }

  resetErrorBoundary = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    const { children, fallback: FallbackComponent } = this.props;

    if (error) {
      return (
        <FallbackComponent
          error={error}
          resetErrorBoundary={this.resetErrorBoundary}
        />
      );
    }

    return children;
  }
}

// ---------------------------------------------------------------------------
// Default loading fallback
// ---------------------------------------------------------------------------

function DefaultLoadingFallback() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="flex gap-4 pt-2">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// QueryBoundary
// ---------------------------------------------------------------------------

export interface QueryBoundaryProps {
  children: ReactNode;
  /** Custom loading fallback (defaults to Skeleton layout) */
  fallback?: ReactNode;
  /** Custom error fallback component (defaults to ErrorFallback) */
  errorFallback?: React.ComponentType<ErrorFallbackProps>;
}

/**
 * Combines React Suspense + ErrorBoundary for data-fetching boundaries.
 *
 * Wraps children with:
 * 1. An ErrorBoundary that catches rendering/query errors
 * 2. A Suspense boundary that shows a loading skeleton
 *
 * @example
 * ```tsx
 * <QueryBoundary>
 *   <ProjectList />
 * </QueryBoundary>
 *
 * <QueryBoundary fallback={<CustomLoader />} errorFallback={CustomError}>
 *   <ProjectDetail />
 * </QueryBoundary>
 * ```
 */
export function QueryBoundary({
  children,
  fallback,
  errorFallback = ErrorFallback,
}: QueryBoundaryProps) {
  return (
    <ErrorBoundary fallback={errorFallback}>
      <Suspense fallback={fallback ?? <DefaultLoadingFallback />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
