"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { AISuggestionReviewCard } from "@/components/ai-generation/AISuggestionReviewCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getQuestionSuggestion } from "@/lib/aiGeneration";
import { getQuestion } from "@/lib/questionBank";
import type { AIQuestionSuggestionRun } from "@/types/aiGeneration";
import type { Question } from "@/types/questionBank";

type AISuggestionDetailContentProps = {
  id: string;
  basePath: string;
};

export function AISuggestionDetailContent({
  id,
  basePath
}: AISuggestionDetailContentProps) {
  const [run, setRun] = useState<AIQuestionSuggestionRun | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [questionError, setQuestionError] = useState("");

  const loadSuggestion = useCallback(async () => {
    setIsLoading(true);
    try {
      const runData = await getQuestionSuggestion(id);
      setRun(runData);
      setError("");

      try {
        setQuestion(await getQuestion(runData.question));
        setQuestionError("");
      } catch (err) {
        setQuestion(null);
        setQuestionError(
          err instanceof ApiError
            ? err.message
            : "Unable to load the linked question."
        );
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load AI suggestion."
      );
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadSuggestion();
  }, [loadSuggestion]);

  async function handleApplied(updatedRun: AIQuestionSuggestionRun) {
    setRun(updatedRun);
    try {
      setQuestion(await getQuestion(updatedRun.question));
      setQuestionError("");
    } catch (err) {
      setQuestionError(
        err instanceof ApiError
          ? err.message
          : "Suggestion was applied, but the question could not be reloaded."
      );
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading AI suggestion..." />;
  }

  if (error && !run) {
    return <EmptyState title="AI suggestion unavailable" description={error} />;
  }

  if (!run) {
    return (
      <EmptyState
        title="AI suggestion not found"
        description="This AI suggestion could not be found or you do not have access."
      />
    );
  }

  const questionHref = `${basePath}/${run.question}`;

  return (
    <>
      <PageHeader
        title="AI Suggestion Review"
        description="Review advisory AI output, then manually apply only the fields you trust."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href={`${basePath}/ai-suggestions`}>
              <Button variant="secondary">Back to AI Suggestions</Button>
            </Link>
            <Link href={questionHref}>
              <Button>Back to Question</Button>
            </Link>
          </div>
        }
      />

      <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
        AI suggestions are advisory. Review carefully before applying.
      </div>

      {questionError ? (
        <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
          {questionError}
        </div>
      ) : null}

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <AISuggestionReviewCard
        run={run}
        question={question}
        questionHref={questionHref}
        onApplied={handleApplied}
      />
    </>
  );
}
