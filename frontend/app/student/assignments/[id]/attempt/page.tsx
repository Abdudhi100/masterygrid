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
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import {
  getMyAssignments,
  startAssignment,
  submitAssignment
} from "@/lib/submissions";
import type {
  StudentAnswerInput,
  StudentAssignmentItem,
  SubmissionStart
} from "@/types/submissions";

type AnswerMap = Record<number, number>;

function draftKey(
  studentId: number | string,
  assignmentId: string,
  submissionId: number | string
) {
  return `masterygrid.answers.${studentId}.${assignmentId}.${submissionId}`;
}

function secondsLabel(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

function AttemptContent({ assignmentId }: { assignmentId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const [submission, setSubmission] = useState<SubmissionStart | null>(null);
  const [assignment, setAssignment] = useState<StudentAssignmentItem | null>(null);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const hasAutoSubmitted = useRef(false);
  const isSubmittingRef = useRef(false);

  useEffect(() => {
    async function loadAttempt() {
      try {
        const [submissionStart, assignmentRows] = await Promise.all([
          startAssignment(assignmentId),
          getMyAssignments()
        ]);
        setSubmission(submissionStart);
        const currentAssignment =
          assignmentRows.find((item) => String(item.id) === assignmentId) ?? null;
        setAssignment(currentAssignment);

        const key = draftKey(user?.id ?? "student", assignmentId, submissionStart.id);
        const saved = window.localStorage.getItem(key);
        if (saved) {
          setAnswers(JSON.parse(saved) as AnswerMap);
        }

        if (currentAssignment?.duration_minutes) {
          setSecondsLeft(currentAssignment.duration_minutes * 60);
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to start or continue this assignment."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAttempt();
  }, [assignmentId, user?.id]);

  const storageKey = submission
    ? draftKey(user?.id ?? "student", assignmentId, submission.id)
    : null;

  useEffect(() => {
    if (storageKey) {
      window.localStorage.setItem(storageKey, JSON.stringify(answers));
    }
  }, [answers, storageKey]);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const totalQuestions = submission?.questions.length ?? 0;

  const submitCurrentAnswers = useCallback(async (auto = false) => {
    if (!submission || isSubmittingRef.current) {
      return;
    }

    if (answeredCount !== totalQuestions) {
      setError("Answer every question before submitting.");
      return;
    }

    if (!auto && !window.confirm("Submit this assignment for final marking?")) {
      return;
    }

    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setError("");
    const payload: StudentAnswerInput[] = submission.questions.map((question) => ({
      assignment_question: question.assignment_question,
      selected_option: answers[question.assignment_question]
    }));

    try {
      const result = await submitAssignment(submission.id, payload);
      if (storageKey) {
        window.localStorage.removeItem(storageKey);
      }
      router.replace(
        `/student/assignments/${assignmentId}/result?submissionId=${result.id}`
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to submit answers.");
    } finally {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
    }
  }, [
    answeredCount,
    answers,
    assignmentId,
    router,
    storageKey,
    submission,
    totalQuestions
  ]);

  useEffect(() => {
    if (secondsLeft === null || secondsLeft <= 0 || isSubmitting) {
      return;
    }

    const timer = window.setInterval(() => {
      setSecondsLeft((current) => (current === null ? null : Math.max(current - 1, 0)));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [isSubmitting, secondsLeft]);

  useEffect(() => {
    if (
      secondsLeft === 0 &&
      !hasAutoSubmitted.current &&
      submission &&
      answeredCount === totalQuestions
    ) {
      hasAutoSubmitted.current = true;
      void submitCurrentAnswers(true);
    }
  }, [
    answeredCount,
    secondsLeft,
    submission,
    submitCurrentAnswers,
    totalQuestions
  ]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitCurrentAnswers(false);
  }

  if (isLoading) {
    return <LoadingState label="Preparing your assignment..." />;
  }

  if (error && !submission) {
    return <EmptyState title="Cannot start assignment" description={error} />;
  }

  if (!submission) {
    return (
      <EmptyState
        title="Assignment unavailable"
        description="This assignment could not be started."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={submission.assignment_title}
        description={`${submission.subject_name} - ${submission.topic_title} - ${submission.class_arm_name}`}
        actions={
          <Link href="/student/assignments">
            <Button variant="secondary">Exit</Button>
          </Link>
        }
      />

      <Card className="mb-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-semibold text-ink">
            Progress: {answeredCount} / {totalQuestions}
          </p>
          <p className="text-sm font-semibold text-muted">
            {secondsLeft !== null
              ? `Time left: ${secondsLabel(secondsLeft)}`
              : assignment?.duration_minutes
                ? `${assignment.duration_minutes} minutes`
                : "No timer"}
          </p>
        </div>
      </Card>

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <form className="space-y-4" onSubmit={handleSubmit}>
        {submission.questions.map((question, index) => (
          <Card key={question.assignment_question}>
            <p className="text-sm font-semibold text-brand-700">
              Question {index + 1} · {question.marks} mark
              {question.marks === 1 ? "" : "s"}
            </p>
            <p className="mt-3 text-base font-medium leading-7 text-ink">
              {question.question_text}
            </p>
            <div className="mt-4 space-y-2">
              {question.options.map((option) => (
                <label
                  key={option.id}
                  className={`flex cursor-pointer gap-3 rounded-md border p-3 text-sm transition ${
                    answers[question.assignment_question] === option.id
                      ? "border-brand-500 bg-brand-50"
                      : "border-line bg-white hover:bg-surface"
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${question.assignment_question}`}
                    className="mt-1"
                    checked={answers[question.assignment_question] === option.id}
                    onChange={() =>
                      setAnswers((current) => ({
                        ...current,
                        [question.assignment_question]: option.id
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
              isLoading={isSubmitting}
              disabled={answeredCount !== totalQuestions}
            >
              Submit Assignment
            </Button>
          </div>
        </div>
      </form>
    </>
  );
}

export default function AssignmentAttemptPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading attempt..." />}>
      <AttemptContent assignmentId={params.id} />
    </Suspense>
  );
}
