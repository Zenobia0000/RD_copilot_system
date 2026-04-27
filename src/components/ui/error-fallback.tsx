import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

/**
 * A shadcn/ui-styled error fallback component.
 *
 * Displays the error message inside a Card with an AlertTriangle icon
 * and a retry button that calls `resetErrorBoundary`.
 */
export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <Card className="mx-auto my-8 max-w-lg border-destructive/50">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0">
        <AlertTriangle className="h-6 w-6 text-destructive" />
        <CardTitle className="text-base text-destructive">Something went wrong</CardTitle>
      </CardHeader>

      <CardContent>
        <p className="text-sm text-muted-foreground">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>

        {process.env.NODE_ENV === 'development' && error.stack && (
          <pre className="mt-4 max-h-40 overflow-auto rounded-md bg-muted p-3 text-xs text-muted-foreground">
            {error.stack}
          </pre>
        )}
      </CardContent>

      <CardFooter>
        <Button variant="outline" size="sm" onClick={resetErrorBoundary} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </CardFooter>
    </Card>
  );
}
