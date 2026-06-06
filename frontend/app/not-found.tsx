import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function NotFoundPage() {
  return (
    <main className="min-h-screen bg-surface px-4 py-12">
      <div className="mx-auto max-w-2xl pt-12">
        <Card className="flex min-h-48 flex-col items-center justify-center text-center">
          <p className="text-sm font-semibold uppercase text-brand-600">404</p>
          <h1 className="mt-2 text-2xl font-semibold text-ink">
            Page not found
          </h1>
          <p className="mt-2 max-w-md text-sm leading-6 text-muted">
            The page you opened is not available. Return to your dashboard or
            use the sidebar to continue.
          </p>
          <Link href="/admin/dashboard" className="mt-4">
            <Button>Go to dashboard</Button>
          </Link>
        </Card>
      </div>
    </main>
  );
}
