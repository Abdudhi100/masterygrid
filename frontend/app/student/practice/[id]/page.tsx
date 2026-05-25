"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FormEvent,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QuestionMediaDisplay } from "@/components/question-bank/QuestionMediaDisplay";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { getPracticeSession, submitPracticeSession } from "@/lib/practice";
import type { PracticeAnswerInput, PracticeSession } from "@/types/practice";

type AnswerMap = Record<number, number>;

function draftKey(studentId: number | string, practiceSessionId: string) {
  return `masterygrid.practice.answers.${studentId}.${practiceSessionId}`;
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function PracticeAttemptContent({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const isSubmittingRef = useRef(false);

  useEffect(() => {
    async function loadPractice() {
      try {
        const sessionData = await getPracticeSession(sessionId);
        setSession(sessionData);
        const key = draftKey(user?.id ?? "student", sessionId);
        const saved = window.localStorage.getItem(key);
        if (saved) {
          const savedAnswers = JSON.parse(saved) as AnswerMap;
          const validQuestionIds = new Set(
            (sessionData.questions ?? []).map((question) =>
              String(question.session_question)
            )
          );
          const filteredAnswers = Object.fromEntries(
            Object.entries(savedAnswers).filter(([questionId]) =>
              validQuestionIds.has(questionId)
            )
          ) as AnswerMap;
          setAnswers(filteredAnswers);
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load this practice session."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadPractice();
  }, [sessionId, user?.id]);

  const storageKey = draftKey(user?.id ?? "student", sessionId);

  useEffect(() => {
    if (session) {
      window.localStorage.setItem(storageKey, JSON.stringify(answers));
    }
  }, [answers, session, storageKey]);

  const questions = useMemo(() => session?.questions ?? [], [session]);
  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const totalQuestions = questions.length;

  const submitCurrentAnswers = useCallback(async () => {
    if (!session || isSubmittingRef.current) {
      return;
    }

    if (session.status !== "in_progress") {
      setError("This practice session has already been submitted.");
      return;
    }

    if (answeredCount !== totalQuestions) {
      setError("Answer every question before submitting.");
      return;
    }

    if (!window.confirm("Submit this practice session for marking?")) {
      return;
    }

    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setError("");

    const payload: PracticeAnswerInput[] = questions.map((question) => ({
      session_question: question.session_question,
      selected_option: answers[question.session_question]
    }));

    try {
      await submitPracticeSession(session.id, payload);
      window.localStorage.removeItem(storageKey);
      router.replace(`/student/practice/${session.id}/result`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to submit practice answers."
      );
    } finally {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
    }
  }, [
    answeredCount,
    answers,
    questions,
    router,
    session,
    storageKey,
    totalQuestions
  ]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitCurrentAnswers();
  }

  if (isLoading) {
    return <LoadingState label="Loading practice session..." />;
  }

  if (error && !session) {
    return <EmptyState title="Practice unavailable" description={error} />;
  }

  if (!session) {
    return (
      <EmptyState
        title="Practice not found"
        description="This practice session could not be found."
      />
    );
  }

  if (session.status === "submitted") {
    return (
      <>
        <PageHeader
          title="Practice Submitted"
          description="This practice session has already been submitted."
        />
        <Card>
          <p className="text-sm leading-6 text-muted">
            You can review your score, corrections, and explanations on the result
            page.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/student/practice">
              <Button variant="secondary">Back to Practice</Button>
            </Link>
            <Link href={`/student/practice/${session.id}/result`}>
              <Button>View Result</Button>
            </Link>
          </div>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={`${session.subject_name} Practice`}
        description={`${session.topic_title ?? "Any topic"} - ${
          session.class_level_name ?? "Any class level"
        } - ${humanize(session.difficulty)}`}
        actions={
          <Link href="/student/practice">
            <Button variant="secondary">Exit Practice</Button>
          </Link>
        }
      />

      <Card className="mb-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-semibold text-ink">
            Progress: {answeredCount} / {totalQuestions}
          </p>
          <Badge tone="warning">{humanize(session.status)}</Badge>
        </div>
      </Card>

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <form className="space-y-4" onSubmit={handleSubmit}>
        {questions.map((question, index) => (
          <Card
            key={question.session_question}
            data-testid="practice-question-card"
          >
            <p className="text-sm font-semibold text-brand-700">
              Question {index + 1} - {question.marks} mark
              {question.marks === 1 ? "" : "s"}
            </p>
            <p className="mt-3 text-base font-medium leading-7 text-ink">
              {question.question_text}
            </p>
            <div className="mt-4" data-testid="practice-question-media">
              <QuestionMediaDisplay media={question.media} compact />
            </div>
            <div className="mt-4 space-y-2">
              {question.options.map((option) => (
                <label
                  key={option.id}
                  className={`flex cursor-pointer gap-3 rounded-md border p-3 text-sm transition ${
                    answers[question.session_question] === option.id
                      ? "border-brand-500 bg-brand-50"
                      : "border-line bg-white hover:bg-surface"
                  }`}
                >
                  <input
                    type="radio"
                    data-testid="practice-option-radio"
                    name={`practice-question-${question.session_question}`}
                    className="mt-1"
                    checked={answers[question.session_question] === option.id}
                    onChange={() =>
                      setAnswers((current) => ({
                        ...current,
                        [question.session_question]: option.id
                      }))
                    }
                  />
                  <span>
                    <span className="font-semibold text-ink">{option.label}.</span>{" "}
                    {option.text}
                  </span>
                </label>
              ))}
            </div>
          </Card>
        ))}

        <div className="sticky bottom-0 rounded-lg border border-line bg-white p-4 shadow-soft">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted">
              Submit is enabled after every question is answered.
            </p>
            <Button
              type="submit"
              data-testid="practice-submit-button"
              isLoading={isSubmitting}
              disabled={answeredCount !== totalQuestions}
            >
              Submit Practice
            </Button>
          </div>
        </div>
      </form>
    </>
  );
}

export default function PracticeAttemptPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading practice..." />}>
      <PracticeAttemptContent sessionId={params.id} />
    </Suspense>
  );
}
