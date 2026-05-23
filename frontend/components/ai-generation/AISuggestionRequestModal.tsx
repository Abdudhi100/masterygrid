"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  AISuggestionTypeBadge
} from "@/components/ai-generation/AISuggestionTypeBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { createQuestionSuggestion } from "@/lib/aiGeneration";
import type { AISuggestionType } from "@/types/aiGeneration";

type AISuggestionRequestModalProps = {
  questionId: number;
  basePath: string;
};

const suggestionOptions: Array<{
  value: AISuggestionType;
  title: string;
  description: string;
}> = [
  {
    value: "topic_difficulty_explanation",
    title: "Suggest topic, difficulty, and explanation",
    description: "Best for imported or incomplete questions that need review."
  },
  {
    value: "explanation_only",
    title: "Suggest explanation only",
    description: "Generate or improve a worked explanation."
  },
  {
    value: "difficulty_only",
    title: "Suggest difficulty only",
    description: "Estimate whether this is easy, medium, or hard."
  },
  {
    value: "duplicate_quality_check",
    title: "Check duplicate/quality issues",
    description: "Flag likely duplicate, ambiguous, or low-quality content."
  }
];

export function AISuggestionRequestModal({
  questionId,
  basePath
}: AISuggestionRequestModalProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<AISuggestionType>(
    "topic_difficulty_explanation"
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function requestSuggestion() {
    setIsSubmitting(true);
    setError("");
    try {
      const run = await createQuestionSuggestion({
        question: questionId,
        suggestion_type: selectedType
      });
      router.push(`${basePath}/ai-suggestions/${run.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to request AI suggestions."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Button type="button" variant="secondary" onClick={() => setIsOpen(true)}>
        Get AI Suggestions
      </Button>

      {isOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4 py-6">
          <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">
                  Get AI Suggestions
                </h2>
                <p className="mt-2 text-sm leading-6 text-muted">
                  AI suggestions are advisory. Review carefully before applying.
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                Close
              </Button>
            </div>

            {error ? (
              <div className="mt-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
                {error}
              </div>
            ) : null}

            <div className="mt-5 space-y-3">
              {suggestionOptions.map((option) => (
                <label
                  key={option.value}
                  className={`block rounded-md border p-4 transition ${
                    selectedType === option.value
                      ? "border-brand-300 bg-brand-50"
                      : "border-line bg-white hover:bg-surface"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="radio"
                      name="suggestion_type"
                      value={option.value}
                      checked={selectedType === option.value}
                      onChange={() => setSelectedType(option.value)}
                      className="mt-1"
                    />
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-ink">
                          {option.title}
                        </span>
                        <AISuggestionTypeBadge type={option.value} />
                      </div>
                      <p className="mt-1 text-sm leading-6 text-muted">
                        {option.description}
                      </p>
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                isLoading={isSubmitting}
                onClick={requestSuggestion}
              >
                Request Suggestions
              </Button>
            </div>
          </Card>
        </div>
      ) : null}
    </>
  );
}
