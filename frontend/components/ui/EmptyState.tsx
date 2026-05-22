import { Card } from "@/components/ui/Card";

export function EmptyState({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="flex min-h-48 flex-col items-center justify-center text-center">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted">{description}</p>
    </Card>
  );
}
