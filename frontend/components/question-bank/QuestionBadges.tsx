import { Badge } from "@/components/ui/Badge";
import type { QuestionDifficulty, QuestionStatus } from "@/types/questionBank";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

const statusTone: Record<QuestionStatus, BadgeTone> = {
  draft: "warning",
  approved: "success",
  rejected: "danger",
  archived: "neutral"
};

const difficultyTone: Record<QuestionDifficulty, BadgeTone> = {
  easy: "success",
  medium: "brand",
  hard: "warning"
};

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

export function QuestionStatusBadge({ status }: { status: QuestionStatus }) {
  return <Badge tone={statusTone[status]}>{humanize(status)}</Badge>;
}

export function QuestionDifficultyBadge({
  difficulty
}: {
  difficulty: QuestionDifficulty;
}) {
  return <Badge tone={difficultyTone[difficulty]}>{humanize(difficulty)}</Badge>;
}
