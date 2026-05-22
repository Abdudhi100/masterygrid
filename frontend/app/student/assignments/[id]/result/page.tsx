"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getSubmissionResult } from "@/lib/submissions";
import type { SubmissionResult } from "@/types/submissions";

function formatDate(value: string | null) {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function timeSpent(seconds: number | null) {
  if (!seconds) {
    return "Not recorded";
  }
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}m ${remaining}s`;
}

function ResultContent() {
  const searchParams = useSearchParams();
  const submissionId = searchParams.get("submissionId");
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadResult() {
      if (!submissionId) {
        setError("Submission ID is required to view this result.");
        setIsLoading(false);
        return;
      }

      try {
        setResult(await getSubmissionResult(submissionId));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load result.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadResult();
  }, [submissionId]);

  if (isLoading) {
    return <LoadingState label="Loading result..." />;
  }

  if (error) {
    return <EmptyState title="Result unavailable" description={error} />;
  }

  if (!result) {
    return (
      <EmptyState
        title="No result found"
        description="This result could not be loaded."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={`${result.assignment_title} Result`}
        description={`${result.subject_name} · ${result.topic_title} · ${result.class_arm_name}`}
        actions={
          <Link href="/student/assignments">
            <Button variant="secondary">Back to My Assignments</Button>
          </Link>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm font-medium text-muted">Score</p>
          <p className="mt-2 text-3xl font-semibold text-ink">
            {result.score}/{result.total_marks}
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-muted">Percentage</p>
          <p className="mt-2 text-3xl font-semibold text-ink">
            {Number(result.percentage).toFixed(2)}%
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-muted">Submitted</p>
          <p className="mt-2 text-sm font-semibold text-ink">
            {formatDate(result.submitted_at)}
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-muted">Time spent</p>
          <p className="mt-2 text-sm font-semibold text-ink">
            {timeSpent(result.time_spent_seconds)}
          </p>
        </Card>
      </section>

      <section className="mt-6 space-y-4">
        <h2 className="text-lg font-semibold text-ink">Correction Review</h2>
        {result.answers.map((answer, index) => (
          <Card key={answer.assignment_question}>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-semibold text-brand-700">
                Question {index + 1}
              </p>
              <Badge tone={answer.is_correct ? "success" : "danger"}>
                {answer.is_correct ? "correct" : "wrong"}
              </Badge>
            </div>
            <p className="mt-3 text-base font-medium leading-7 text-ink">
              {answer.question_text}
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-md border border-line bg-surface p-3">
                <p className="text-xs font-semibold uppercase text-muted">
                  Your answer
                </p>
                <p className="mt-1 text-sm text-ink">
                  {answer.selected_option
                    ? `${answer.selected_option.label}. ${answer.selected_option.text}`
                    : "No answer"}
                </p>
              </div>
              <div className="rounded-md border border-line bg-surface p-3">
                <p className="text-xs font-semibold uppercase text-muted">
                  Correct answer
                </p>
                <p className="mt-1 text-sm text-ink">
                  {answer.correct_option
                    ? `${answer.correct_option.label}. ${answer.correct_option.text}`
                    : "Not available"}
                </p>
              </div>
            </div>
            <p className="mt-3 text-sm font-semibold text-muted">
              Marks awarded: {answer.marks_awarded}
            </p>
            {answer.explanation ? (
              <p className="mt-3 rounded-md bg-brand-50 p-3 text-sm leading-6 text-brand-700">
                {answer.explanation}
              </p>
            ) : null}
          </Card>
        ))}
      </section>
    </>
  );
}

export default function AssignmentResultPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading result..." />}>
      <ResultContent />
    </Suspense>
  );
}
