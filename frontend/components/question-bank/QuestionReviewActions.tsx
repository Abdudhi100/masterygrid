"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api";
import {
  approveQuestion,
  archiveQuestion,
  rejectQuestion
} from "@/lib/questionBank";
import type { Question } from "@/types/questionBank";

type QuestionReviewActionsProps = {
  question: Question;
  canReview: boolean;
  onQuestionChange: (question: Question) => void;
  onError?: (message: string) => void;
  onSuccess?: (message: string) => void;
};

type ActionName = "approve" | "reject" | "archive";

export function QuestionReviewActions({
  question,
  canReview,
  onQuestionChange,
  onError,
  onSuccess
}: QuestionReviewActionsProps) {
  const [loadingAction, setLoadingAction] = useState<ActionName | null>(null);

  if (!canReview) {
    return null;
  }

  async function runAction(
    actionName: ActionName,
    action: (id: number) => Promise<Question>,
    message: string
  ) {
    setLoadingAction(actionName);
    onError?.("");
    onSuccess?.("");

    try {
      const updated = await action(question.id);
      onQuestionChange(updated);
      onSuccess?.(message);
    } catch (err) {
      onError?.(
        err instanceof ApiError ? err.message : "Unable to update question."
      );
    } finally {
      setLoadingAction(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {question.status === "draft" ? (
        <>
          <Button
            isLoading={loadingAction === "approve"}
            onClick={() =>
              runAction("approve", approveQuestion, "Question approved.")
            }
          >
            Approve
          </Button>
          <Button
            variant="secondary"
            isLoading={loadingAction === "reject"}
            onClick={() =>
              runAction("reject", rejectQuestion, "Question rejected.")
            }
          >
            Reject
          </Button>
        </>
      ) : null}
      {question.status !== "archived" ? (
        <Button
          variant="ghost"
          isLoading={loadingAction === "archive"}
          onClick={() =>
            runAction("archive", archiveQuestion, "Question archived.")
          }
        >
          Archive
        </Button>
      ) : null}
    </div>
  );
}
