"use client";

import { ErrorState } from "@/components/ui/ErrorState";

export default function GlobalError({
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-surface px-4 py-12">
      <div className="mx-auto max-w-2xl pt-12">
        <ErrorState
          title="MasteryGrid hit a snag"
          description="Something went wrong while loading this page. Try again, or return to your dashboard."
          onRetry={reset}
        />
      </div>
    </main>
  );
}
