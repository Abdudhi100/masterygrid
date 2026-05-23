"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import {
  AISuggestionStatusBadge
} from "@/components/ai-generation/AISuggestionStatusBadge";
import {
  AISuggestionTypeBadge
} from "@/components/ai-generation/AISuggestionTypeBadge";
import { QuestionDifficultyBadge } from "@/components/question-bank/QuestionBadges";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { applyQuestionSuggestion } from "@/lib/aiGeneration";
import type { AIQuestionSuggestionRun } from "@/types/aiGeneration";
import type { Question } from "@/types/questionBank";

type ApplyField = "topic" | "difficulty" | "explanation";

type AISuggestionReviewCardProps = {
  run: AIQuestionSuggestionRun;
  question: Question | null;
  questionHref: string;
  onApplied: (run: AIQuestionSuggestionRun) => void;
};

function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatConfidence(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "Not provided";
  }

  return `${Math.round(value * 100)}%`;
}

function fieldLabel(field: ApplyField) {
  const labels: Record<ApplyField, string> = {
    topic: "Apply topic",
    difficulty: "Apply difficulty",
    explanation: "Apply explanation"
  };
  return labels[field];
}

export function AISuggestionReviewCard({
  run,
  question,
  questionHref,
  onApplied
}: AISuggestionReviewCardProps) {
  const [selectedFields, setSelectedFields] = useState<ApplyField[]>([]);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const availableFields = useMemo(() => {
    const fields: ApplyField[] = [];
    if (run.suggested_topic) {
      fields.push("topic");
    }
    if (run.suggested_difficulty) {
      fields.push("difficulty");
    }
    if (run.suggested_explanation) {
      fields.push("explanation");
    }
    return fields;
  }, [run.suggested_difficulty, run.suggested_explanation, run.suggested_topic]);

  function toggleField(field: ApplyField) {
    setSelectedFields((current) =>
      current.includes(field)
        ? current.filter((item) => item !== field)
        : [...current, field]
    );
  }

  async function applySelectedSuggestions() {
    setIsApplying(true);
    setError("");
    setSuccess("");
    try {
      const response = await applyQuestionSuggestion(run.id, selectedFields);
      onApplied(response.run);
      setSuccess("Selected AI suggestions were applied.");
      setSelectedFields([]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to apply selected suggestions."
      );
    } finally {
      setIsApplying(false);
    }
  }

  const canApply =
    run.status === "succeeded" && selectedFields.length > 0 && !isApplying;

  return (
    <div className="space-y-6">
      {success ? (
        <div className="rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-success">
          {success}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="flex flex-wrap gap-2">
              <AISuggestionStatusBadge status={run.status} />
              <AISuggestionTypeBadge type={run.suggestion_type} />
              {run.applied_at ? <Badge tone="success">applied</Badge> : null}
            </div>
            <p className="mt-4 whitespace-pre-wrap text-base font-medium leading-7 text-ink">
              {question?.question_text ?? run.question_text ?? "Question unavailable"}
            </p>
          </div>
          <Link href={questionHref}>
            <Button variant="secondary">Back to Question</Button>
          </Link>
        </div>

        <dl className="mt-6 grid gap-4 text-sm text-muted sm:grid-cols-2 xl:grid-cols-4">
          <div>
            <dt className="font-semibold text-ink">Current topic</dt>
            <dd className="mt-1">
              {question?.topic_title ??
                run.current_topic_title ??
                run.question_topic ??
                "Not set"}
            </dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Current difficulty</dt>
            <dd className="mt-1">
              {question?.difficulty ? (
                <QuestionDifficultyBadge difficulty={question.difficulty} />
              ) : (
                run.current_difficulty ?? "Not set"
              )}
            </dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Requested by</dt>
            <dd className="mt-1">{run.requested_by_name ?? "Unknown"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Confidence</dt>
            <dd className="mt-1">{formatConfidence(run.confidence_score)}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Created</dt>
            <dd className="mt-1">{formatDate(run.created_at)}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Completed</dt>
            <dd className="mt-1">{formatDate(run.completed_at)}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Applied by</dt>
            <dd className="mt-1">{run.applied_by_name ?? "Not applied"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Applied at</dt>
            <dd className="mt-1">{formatDate(run.applied_at)}</dd>
          </div>
        </dl>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink">
            Current Explanation
          </h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">
            {question?.explanation ??
              run.current_explanation ??
              "No current explanation available."}
          </p>
        </Card>
        <Card>
          <h2 className="text-base font-semibold text-ink">
            Suggested Explanation
          </h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">
            {run.suggested_explanation || "No explanation suggestion returned."}
          </p>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="text-base font-semibold text-ink">Suggested Topic</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            {run.suggested_topic_title ||
              "No existing topic matched the AI suggestion."}
          </p>
        </Card>
        <Card>
          <h2 className="text-base font-semibold text-ink">
            Suggested Difficulty
          </h2>
          <div className="mt-3">
            {run.suggested_difficulty ? (
              <QuestionDifficultyBadge difficulty={run.suggested_difficulty} />
            ) : (
              <p className="text-sm text-muted">No difficulty suggestion returned.</p>
            )}
          </div>
        </Card>
        <Card>
          <h2 className="text-base font-semibold text-ink">Provider</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            {run.provider} / {run.model_name}
          </p>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className={run.duplicate_warning ? "border-amber-200 bg-amber-50" : ""}>
          <h2 className="text-base font-semibold text-ink">Duplicate Warning</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">
            {run.duplicate_warning || "No duplicate warning returned."}
          </p>
        </Card>
        <Card className={run.quality_warning ? "border-amber-200 bg-amber-50" : ""}>
          <h2 className="text-base font-semibold text-ink">Quality Warning</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">
            {run.quality_warning || "No quality warning returned."}
          </p>
        </Card>
      </section>

      {run.error_message ? (
        <Card className="border-red-200 bg-red-50">
          <h2 className="text-base font-semibold text-ink">AI Error</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-danger">
            {run.error_message}
          </p>
        </Card>
      ) : null}

      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">
              Apply Selected Suggestions
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              AI suggestions are advisory. Review carefully before applying.
            </p>
          </div>
          <Button
            type="button"
            isLoading={isApplying}
            disabled={!canApply}
            onClick={applySelectedSuggestions}
          >
            Apply Selected Suggestions
          </Button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {(["topic", "difficulty", "explanation"] as ApplyField[]).map((field) => {
            const isAvailable = availableFields.includes(field);
            return (
              <label
                key={field}
                className={`rounded-md border p-4 text-sm ${
                  isAvailable ? "border-line bg-white" : "border-line bg-surface"
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={selectedFields.includes(field)}
                    disabled={!isAvailable || run.status !== "succeeded"}
                    onChange={() => toggleField(field)}
                    className="mt-1"
                  />
                  <div>
                    <span className="font-semibold text-ink">
                      {fieldLabel(field)}
                    </span>
                    {!isAvailable ? (
                      <p className="mt-1 leading-6 text-muted">
                        No applicable suggestion is available for this field.
                      </p>
                    ) : null}
                  </div>
                </div>
              </label>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
