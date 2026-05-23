import { Badge } from "@/components/ui/Badge";
import type { AISuggestionStatus } from "@/types/aiGeneration";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

const statusTone: Record<AISuggestionStatus, BadgeTone> = {
  pending: "warning",
  processing: "brand",
  succeeded: "success",
  failed: "danger"
};

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

export function AISuggestionStatusBadge({
  status
}: {
  status: AISuggestionStatus;
}) {
  return <Badge tone={statusTone[status]}>{humanize(status)}</Badge>;
}
