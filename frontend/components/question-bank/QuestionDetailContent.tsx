"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AISuggestionRequestModal } from "@/components/ai-generation/AISuggestionRequestModal";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  QuestionDifficultyBadge,
  QuestionStatusBadge
} from "@/components/question-bank/QuestionBadges";
import { QuestionForm } from "@/components/question-bank/QuestionForm";
import { QuestionMediaDisplay } from "@/components/question-bank/QuestionMediaDisplay";
import { QuestionReviewActions } from "@/components/question-bank/QuestionReviewActions";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import {
  createQuestionMedia,
  deleteQuestionMedia,
  getQuestion,
  updateQuestion
} from "@/lib/questionBank";
import type { CurrentUser } from "@/types/auth";
import type { Question, QuestionPayload } from "@/types/questionBank";

type QuestionDetailContentProps = {
  id: string;
  mode: "admin" | "teacher";
  basePath: string;
};

function formatDate(value?: string | null) {
  if (!value) {
    return "Not reviewed";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not reviewed";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function isPlatformAdmin(user: CurrentUser | null) {
  return Boolean(
    user && (user.role === "platform_admin" || user.is_superuser)
  );
}

function canEditQuestion(
  question: Question,
  mode: "admin" | "teacher",
  user: CurrentUser | null
) {
  if (isPlatformAdmin(user)) {
    return ["draft", "rejected"].includes(question.status);
  }

  if (mode === "admin") {
    return question.school !== null && ["draft", "rejected"].includes(question.status);
  }

  return question.status === "draft" && question.created_by === user?.id;
}

function canReviewQuestion(
  question: Question,
  mode: "admin" | "teacher",
  user: CurrentUser | null
) {
  if (mode !== "admin") {
    return false;
  }

  return isPlatformAdmin(user) || question.school !== null;
}

function canManageMedia(
  question: Question,
  mode: "admin" | "teacher",
  user: CurrentUser | null
) {
  if (isPlatformAdmin(user)) {
    return true;
  }

  if (mode === "admin") {
    return question.school !== null && question.school === user?.school;
  }

  return question.status === "draft" && question.created_by === user?.id;
}

export function QuestionDetailContent({
  id,
  mode,
  basePath
}: QuestionDetailContentProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [question, setQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [mediaDescription, setMediaDescription] = useState("");
  const [mediaAltText, setMediaAltText] = useState("");
  const [mediaCaption, setMediaCaption] = useState("");
  const [mediaNeedsReview, setMediaNeedsReview] = useState(false);
  const [isAddingMedia, setIsAddingMedia] = useState(false);
  const [deletingMediaId, setDeletingMediaId] = useState<number | null>(null);
  const isEditing = searchParams.get("mode") === "edit";

  const loadQuestion = useCallback(async () => {
    try {
      setQuestion(await getQuestion(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load question.");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadQuestion();
  }, [loadQuestion]);

  const sortedOptions = useMemo(() => {
    return [...(question?.options ?? [])].sort((a, b) =>
      a.label.localeCompare(b.label)
    );
  }, [question]);

  async function handleAddMedia() {
    if (!question) {
      return;
    }

    setError("");
    setSuccess("");
    if (!mediaUrl.trim()) {
      setError("Enter a diagram URL.");
      return;
    }

    try {
      new URL(mediaUrl.trim());
    } catch {
      setError("Enter a valid diagram URL.");
      return;
    }

    setIsAddingMedia(true);
    try {
      await createQuestionMedia(question.id, {
        external_url: mediaUrl.trim(),
        description: mediaDescription.trim(),
        alt_text: mediaAltText.trim() || mediaDescription.trim(),
        caption: mediaCaption.trim(),
        is_primary: question.media.length === 0,
        needs_manual_review: mediaNeedsReview
      });
      setMediaUrl("");
      setMediaDescription("");
      setMediaAltText("");
      setMediaCaption("");
      setMediaNeedsReview(false);
      setSuccess("Diagram media added.");
      await loadQuestion();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to add diagram media.");
    } finally {
      setIsAddingMedia(false);
    }
  }

  async function handleDeleteMedia(mediaId: number) {
    if (!window.confirm("Remove this diagram from the question?")) {
      return;
    }

    setError("");
    setSuccess("");
    setDeletingMediaId(mediaId);
    try {
      await deleteQuestionMedia(mediaId);
      setSuccess("Diagram media removed.");
      await loadQuestion();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to remove diagram media."
      );
    } finally {
      setDeletingMediaId(null);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading question..." />;
  }

  if (error && !question) {
    return <EmptyState title="Question unavailable" description={error} />;
  }

  if (!question) {
    return (
      <EmptyState
        title="Question not found"
        description="This question could not be found or you do not have access."
      />
    );
  }

  if (isEditing) {
    if (!canEditQuestion(question, mode, user)) {
      return (
        <EmptyState
          title="Question cannot be edited"
          description="Only editable draft or rejected questions can be changed from this page."
        />
      );
    }

    return (
      <>
        <PageHeader
          title="Edit Question"
          description="Update the question text, topic, difficulty, explanation, or options."
        />
        <QuestionForm
          initialQuestion={question}
          submitLabel="Save Question"
          cancelHref={`${basePath}/${question.id}`}
          onSubmit={(payload: QuestionPayload) => updateQuestion(question.id, payload)}
          onSaved={(updatedQuestion) => {
            setQuestion(updatedQuestion);
            setSuccess("Question updated.");
            router.replace(`${basePath}/${updatedQuestion.id}`);
          }}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Question Detail"
        description={`${question.subject_name ?? "Subject"} - ${
          question.topic_title ?? "Topic"
        } - ${question.class_level_name ?? "Class level"}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href={`${basePath}/ai-suggestions`}>
              <Button variant="secondary">AI Suggestions</Button>
            </Link>
            <Link href={basePath}>
              <Button variant="secondary">Back to Question Bank</Button>
            </Link>
          </div>
        }
      />

      {mode === "teacher" ? (
        <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
          Teacher-created questions may require school admin approval before they can
          be used in assignments.
        </div>
      ) : null}
      {success ? (
        <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-success">
          {success}
        </div>
      ) : null}
      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              <QuestionStatusBadge status={question.status} />
              <QuestionDifficultyBadge difficulty={question.difficulty} />
              {question.school_name ? (
                <Badge tone="brand">{question.school_name}</Badge>
              ) : (
                <Badge tone="success">global</Badge>
              )}
              {question.has_diagram ? <Badge tone="brand">has diagram</Badge> : null}
              {question.needs_manual_review ? (
                <Badge tone="warning">needs manual review</Badge>
              ) : null}
            </div>
            <p className="mt-4 whitespace-pre-wrap text-base font-medium leading-7 text-ink">
              {question.question_text}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <AISuggestionRequestModal
              questionId={question.id}
              basePath={basePath}
            />
            {canEditQuestion(question, mode, user) ? (
              <Link href={`${basePath}/${question.id}?mode=edit`}>
                <Button variant="secondary">Edit</Button>
              </Link>
            ) : null}
            <QuestionReviewActions
              question={question}
              canReview={canReviewQuestion(question, mode, user)}
              onQuestionChange={setQuestion}
              onError={setError}
              onSuccess={setSuccess}
            />
          </div>
        </div>

        <dl className="mt-6 grid gap-4 text-sm text-muted sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="font-semibold text-ink">Subject</dt>
            <dd className="mt-1">{question.subject_name ?? "Not set"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Topic</dt>
            <dd className="mt-1">{question.topic_title ?? "Not set"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Class level</dt>
            <dd className="mt-1">{question.class_level_name ?? "Not set"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Source</dt>
            <dd className="mt-1">{question.source_name ?? "No source"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Created by</dt>
            <dd className="mt-1">{question.created_by_name ?? "System"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Reviewed by</dt>
            <dd className="mt-1">{question.reviewed_by_name ?? "Not reviewed"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Reviewed at</dt>
            <dd className="mt-1">{formatDate(question.reviewed_at)}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Active</dt>
            <dd className="mt-1">{question.is_active ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Diagram</dt>
            <dd className="mt-1">{question.has_diagram ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink">Manual review</dt>
            <dd className="mt-1">{question.needs_manual_review ? "Yes" : "No"}</dd>
          </div>
        </dl>
      </Card>

      <section className="mt-6">
        <Card>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">Media</h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                Add or review diagrams linked to this question.
              </p>
            </div>
            {question.has_diagram ? <Badge tone="brand">Diagram</Badge> : null}
          </div>

          {question.diagram_description ? (
            <p className="mt-4 rounded-md bg-surface p-3 text-sm leading-6 text-muted">
              {question.diagram_description}
            </p>
          ) : null}

          <div className="mt-4">
            <QuestionMediaDisplay
              media={question.media}
              diagramDescription={question.diagram_description}
              hasDiagram={question.has_diagram}
            />
          </div>

          {question.media.length > 0 && canManageMedia(question, mode, user) ? (
            <div className="mt-4 space-y-2">
              {question.media.map((item) => (
                <div
                  key={item.id}
                  className="flex flex-col gap-2 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <span className="text-sm text-muted">
                    {item.caption || item.description || item.external_url || "Diagram"}
                  </span>
                  <Button
                    type="button"
                    variant="danger"
                    isLoading={deletingMediaId === item.id}
                    onClick={() => void handleDeleteMedia(item.id)}
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
          ) : null}

          {canManageMedia(question, mode, user) ? (
            <div className="mt-6 rounded-md border border-line bg-white p-4">
              <h3 className="text-sm font-semibold text-ink">
                Add diagram by URL
              </h3>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <Input
                  label="Diagram URL"
                  type="url"
                  value={mediaUrl}
                  placeholder="https://example.com/diagram.png"
                  onChange={(event) => setMediaUrl(event.target.value)}
                />
                <Input
                  label="Caption"
                  value={mediaCaption}
                  onChange={(event) => setMediaCaption(event.target.value)}
                />
                <Input
                  label="Alt text"
                  value={mediaAltText}
                  onChange={(event) => setMediaAltText(event.target.value)}
                />
                <label className="flex items-start gap-3 rounded-md border border-line bg-surface p-3 text-sm text-ink">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={mediaNeedsReview}
                    onChange={(event) => setMediaNeedsReview(event.target.checked)}
                  />
                  <span>
                    <span className="block font-semibold">Needs manual review</span>
                    <span className="mt-1 block text-muted">
                      Mark unclear or externally sourced diagrams for review.
                    </span>
                  </span>
                </label>
              </div>
              <label className="mt-4 block">
                <span className="mb-2 block text-sm font-medium text-ink">
                  Description
                </span>
                <textarea
                  className="min-h-20 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
                  value={mediaDescription}
                  onChange={(event) => setMediaDescription(event.target.value)}
                />
              </label>
              <Button
                type="button"
                className="mt-4"
                isLoading={isAddingMedia}
                onClick={() => void handleAddMedia()}
              >
                Add Diagram
              </Button>
            </div>
          ) : null}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2">
        {sortedOptions.map((option) => (
          <Card key={option.label}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-brand-700">
                Option {option.label}
              </p>
              {option.is_correct ? <Badge tone="success">correct</Badge> : null}
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink">
              {option.text}
            </p>
          </Card>
        ))}
      </section>

      <section className="mt-6">
        <Card>
          <h2 className="text-base font-semibold text-ink">Explanation</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">
            {question.explanation || "No explanation provided."}
          </p>
        </Card>
      </section>
    </>
  );
}
