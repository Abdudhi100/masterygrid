import { Badge } from "@/components/ui/Badge";
import type { AISuggestionType } from "@/types/aiGeneration";

const typeLabel: Record<AISuggestionType, string> = {
  topic_difficulty_explanation: "Topic, difficulty, explanation",
  explanation_only: "Explanation only",
  difficulty_only: "Difficulty only",
  duplicate_quality_check: "Quality check"
};

export function AISuggestionTypeBadge({ type }: { type: AISuggestionType }) {
  return <Badge tone="brand">{typeLabel[type]}</Badge>;
}
