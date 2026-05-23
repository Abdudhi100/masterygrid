"use client";

import { useCallback, useEffect, useState } from "react";
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
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import { getQuestionSuggestions } from "@/lib/aiGeneration";
import type {
  AIQuestionSuggestionFilters,
  AIQuestionSuggestionRun,
  AISuggestionStatus,
  AISuggestionType
} from "@/types/aiGeneration";

type AISuggestionHistoryProps = {
  basePath: string;
};

const statusOptions: Array<{ value: AISuggestionStatus | ""; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "succeeded", label: "Succeeded" },
  { value: "failed", label: "Failed" }
];

const typeOptions: Array<{ value: AISuggestionType | ""; label: string }> = [
  { value: "", label: "All suggestion types" },
  {
    value: "topic_difficulty_explanation",
    label: "Topic, difficulty, explanation"
  },
  { value: "explanation_only", label: "Explanation only" },
  { value: "difficulty_only", label: "Difficulty only" },
  { value: "duplicate_quality_check", label: "Quality check" }
];

function truncate(value = "", limit = 120) {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit)}...`;
}

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

export function AISuggestionHistory({
  basePath
}: AISuggestionHistoryProps) {
  const [runs, setRuns] = useState<AIQuestionSuggestionRun[]>([]);
  const [filters, setFilters] = useState<AIQuestionSuggestionFilters>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSuggestions = useCallback(async () => {
    setIsLoading(true);
    try {
      setRuns(await getQuestionSuggestions(filters));
      setError("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load AI suggestions."
      );
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadSuggestions();
  }, [loadSuggestions]);

  function setFilter(name: keyof AIQuestionSuggestionFilters, value: string) {
    setFilters((current) => ({
      ...current,
      [name]: value
    }));
  }

  if (isLoading && !runs.length) {
    return <LoadingState label="Loading AI suggestions..." />;
  }

  if (error && !runs.length) {
    return <EmptyState title="AI suggestions unavailable" description={error} />;
  }

  return (
    <>
      <Card className="mb-4">
        <p className="text-sm leading-6 text-muted">
          AI suggestions are advisory. Review carefully before applying them to
          question-bank records.
        </p>
      </Card>

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card className="mb-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Select
            label="Status"
            value={String(filters.status ?? "")}
            options={statusOptions}
            onChange={(event) => setFilter("status", event.target.value)}
          />
          <Select
            label="Suggestion type"
            value={String(filters.suggestion_type ?? "")}
            options={typeOptions}
            onChange={(event) =>
              setFilter("suggestion_type", event.target.value)
            }
          />
        </div>
        <div className="mt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setFilters({})}
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      {isLoading ? (
        <LoadingState label="Refreshing AI suggestions..." />
      ) : (
        <DataTable<AIQuestionSuggestionRun>
          data={runs}
          emptyTitle="No AI suggestions yet"
          emptyDescription="Open a question and request AI suggestions to see them here."
          columns={[
            {
              key: "question_text",
              header: "Question",
              render: (row) => (
                <span className="block min-w-[18rem] max-w-xl leading-6">
                  {truncate(row.question_text)}
                </span>
              )
            },
            {
              key: "suggestion_type",
              header: "Type",
              render: (row) => (
                <AISuggestionTypeBadge type={row.suggestion_type} />
              )
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <AISuggestionStatusBadge status={row.status} />
            },
            {
              key: "suggested_topic_title",
              header: "Suggested topic",
              render: (row) => row.suggested_topic_title ?? "Not matched"
            },
            {
              key: "suggested_difficulty",
              header: "Suggested difficulty",
              render: (row) =>
                row.suggested_difficulty ? (
                  <QuestionDifficultyBadge difficulty={row.suggested_difficulty} />
                ) : (
                  "Not suggested"
                )
            },
            {
              key: "confidence_score",
              header: "Confidence",
              render: (row) => formatConfidence(row.confidence_score)
            },
            {
              key: "requested_by_name",
              header: "Requested by",
              render: (row) => row.requested_by_name ?? "Unknown"
            },
            {
              key: "applied_at",
              header: "Applied",
              render: (row) =>
                row.applied_at ? <Badge tone="success">applied</Badge> : "Not applied"
            },
            {
              key: "created_at",
              header: "Created",
              render: (row) => formatDate(row.created_at)
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <Link href={`${basePath}/ai-suggestions/${row.id}`}>
                  <Button variant="secondary">View</Button>
                </Link>
              )
            }
          ]}
        />
      )}
    </>
  );
}
