import { Badge } from "@/components/ui/Badge";
import type {
  QuestionImportFileType,
  QuestionImportRowStatus,
  QuestionImportStatus
} from "@/types/questionBank";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

const batchTone: Record<QuestionImportStatus, BadgeTone> = {
  uploaded: "neutral",
  processing: "brand",
  completed: "success",
  completed_with_errors: "warning",
  failed: "danger"
};

const rowTone: Record<QuestionImportRowStatus, BadgeTone> = {
  pending: "neutral",
  imported: "success",
  failed: "danger",
  duplicate: "warning"
};

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

export function QuestionImportStatusBadge({
  status
}: {
  status: QuestionImportStatus;
}) {
  return <Badge tone={batchTone[status]}>{humanize(status)}</Badge>;
}

export function QuestionImportRowStatusBadge({
  status
}: {
  status: QuestionImportRowStatus;
}) {
  return <Badge tone={rowTone[status]}>{humanize(status)}</Badge>;
}

export function QuestionImportFileTypeBadge({
  fileType
}: {
  fileType: QuestionImportFileType;
}) {
  const tone: BadgeTone = fileType === "zip" ? "brand" : "neutral";
  return <Badge tone={tone}>{fileType.toUpperCase()}</Badge>;
}
