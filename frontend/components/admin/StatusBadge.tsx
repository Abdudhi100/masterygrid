import { Badge } from "@/components/ui/Badge";

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const tone =
    normalized.includes("active") || normalized.includes("approved")
      ? "success"
      : normalized.includes("draft") || normalized.includes("pending")
        ? "warning"
        : "neutral";

  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
