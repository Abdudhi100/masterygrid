import { Badge } from "@/components/ui/Badge";

export function BooleanBadge({
  value,
  trueLabel = "Active",
  falseLabel = "Inactive"
}: {
  value: boolean;
  trueLabel?: string;
  falseLabel?: string;
}) {
  return (
    <Badge tone={value ? "success" : "neutral"}>
      {value ? trueLabel : falseLabel}
    </Badge>
  );
}
