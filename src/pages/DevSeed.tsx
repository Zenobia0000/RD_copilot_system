/**
 * Dev-only page for seeding showcase projects into Supabase.
 * Access at /dev/seed — only visible in development mode.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { seedShowcaseProjects, clearAllShowcaseData } from "@/hooks/api";

export default function DevSeed() {
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleSeed = async () => {
    setLoading(true);
    setStatus("Seeding 3 showcase projects...");
    try {
      const ids = await seedShowcaseProjects();
      setStatus(`Done! Created ${ids.length} projects:\n${ids.join("\n")}`);
    } catch (e: any) {
      setStatus(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    setLoading(true);
    setStatus("Clearing all showcase data...");
    try {
      await clearAllShowcaseData();
      setStatus("All showcase data cleared.");
    } catch (e: any) {
      setStatus(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell-narrow py-10">
      <Card>
        <CardHeader>
          <CardTitle>Dev Seed Tool</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Seed 3 showcase projects at different lifecycle stages into Supabase.
          </p>
          <div className="flex gap-3">
            <Button onClick={handleSeed} disabled={loading}>
              Seed Showcase Projects
            </Button>
            <Button variant="destructive" onClick={handleClear} disabled={loading}>
              Clear All Showcase
            </Button>
          </div>
          {status && (
            <pre className="mt-4 p-3 bg-muted rounded text-xs whitespace-pre-wrap">
              {status}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
