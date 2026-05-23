"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QuestionMediaDisplay } from "@/components/question-bank/QuestionMediaDisplay";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getPracticeResult } from "@/lib/practice";
import type { PracticeResult } from "@/types/practice";

function formatDate(value: string | null) {
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

function percentageLabel(value: string | number | null) {
  if (value === null || value === undefined || value === "") {
    return "0.00%";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "0.00%";
  }

  return `${numeric.toFixed(2)}%`;
}

function PracticeResultContent({ sessionId }: { sessionId: string }) {
  const [result, setResult] = useState<PracticeResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadResult() {
      try {
        setResult(await getPracticeResult(sessionId));
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load practice result."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadResult();
  }, [sessionId]);

  if (isLoading) {
    return <LoadingState label="Loading practice result..." />;
  }

  if (error) {
    return <EmptyState title="Practice result unavailable" description={error} />;
  }

  if (!result) {
    return (
      <EmptyState
        title="No practice result found"
        description="This practice result could not be loaded."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={`${result.subject_name} Practice Result`}
        description={`${result.topic_title ?? "Any topic"} - ${
          result.class_level_name ?? "Any class level"
        }`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/student/practice">
              <Button variant="secondary">Back to Practice</Button>
            </Link>
            <Link href="/student/practice">
              <Button>Practise Again</Button>
            </Link>
          </div>
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
            {percentageLabel(result.percentage)}
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-muted">Difficulty</p>
          <p className="mt-2 text-sm font-semibold capitalize text-ink">
            {result.difficulty.replaceAll("_", " ")}
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-muted">Submitted</p>
          <p className="mt-2 text-sm font-semibold text-ink">
            {formatDate(result.submitted_at)}
          </p>
        </Card>
      </section>

      <section className="mt-6 space-y-4">
        <h2 className="text-lg font-semibold text-ink">Correction Review</h2>
        {result.answers.map((answer, index) => (
          <Card key={answer.session_question}>
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
            {/* TODO: Backend practice result payload needs media snapshot exposure. */}
            <div className="mt-4">
              <QuestionMediaDisplay media={answer.media} compact />
            </div>
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

export default function PracticeResultPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading practice result..." />}>
      <PracticeResultContent sessionId={params.id} />
    </Suspense>
  );
}
