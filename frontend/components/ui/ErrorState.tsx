import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function ErrorState({
  title = "Something went wrong",
  description,
  retryLabel = "Try again",
  onRetry,
  dashboardHref = "/admin/dashboard"
}: {
  title?: string;
  description: string;
  retryLabel?: string;
  onRetry?: () => void;
  dashboardHref?: string;
}) {
  return (
    <Card className="flex min-h-48 flex-col items-center justify-center text-center">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted">{description}</p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {onRetry ? (
          <Button onClick={onRetry} type="button">
            {retryLabel}
          </Button>
        ) : null}
        <Link href={dashboardHref}>
          <Button variant={onRetry ? "secondary" : "primary"}>
            Go to dashboard
          </Button>
        </Link>
      </div>
    </Card>
  );
}
