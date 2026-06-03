"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  archiveAssignment,
  closeAssignment,
  extendAssignmentDeadline,
  getAssignment,
  publishAssignment,
  reopenAssignment
} from "@/lib/academics";
import {
  deadlineStatusTone,
  formatDeadlineStatus
} from "@/lib/assignmentDeadlines";
import { ApiError } from "@/lib/api";
import type { Assignment, AssignmentStatus } from "@/types/academics";

const statusTone: Record<AssignmentStatus, "neutral" | "success" | "warning" | "danger" | "brand"> = {
  draft: "warning",
  published: "success",
  closed: "neutral",
  archived: "danger"
};

function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function localDateTimeValue(value?: string | null) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

export default function AssignmentDetailPage({
  params
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [deadlineDueAt, setDeadlineDueAt] = useState("");
  const [deadlineAllowLate, setDeadlineAllowLate] = useState(false);
  const [deadlineLateUntil, setDeadlineLateUntil] = useState("");
  const deadlineDueAtRef = useRef<HTMLInputElement>(null);
  const deadlineAllowLateRef = useRef<HTMLInputElement>(null);
  const deadlineLateUntilRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadAssignment = useCallback(async () => {
    setError("");
    try {
      setAssignment(await getAssignment(params.id));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load assignment."
      );
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadAssignment();
  }, [loadAssignment]);

  async function runAction(action: (id: string) => Promise<Assignment>, message: string) {
    setIsMutating(true);
    setError("");
    setSuccess("");
    try {
      const updated = await action(params.id);
      setAssignment(updated);
      setDeadlineDueAt(localDateTimeValue(updated.due_at));
      setDeadlineAllowLate(updated.allow_late_submissions);
      setDeadlineLateUntil(localDateTimeValue(updated.late_submission_deadline));
      setSuccess(message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
    } finally {
      setIsMutating(false);
    }
  }

  useEffect(() => {
    if (!assignment) {
      return;
    }
    setDeadlineDueAt(localDateTimeValue(assignment.due_at));
    setDeadlineAllowLate(assignment.allow_late_submissions);
    setDeadlineLateUntil(localDateTimeValue(assignment.late_submission_deadline));
  }, [assignment]);

  function validateDeadlineForm() {
    const currentDueAt = deadlineDueAtRef.current?.value ?? deadlineDueAt;
    const currentAllowLate =
      deadlineAllowLateRef.current?.checked ?? deadlineAllowLate;
    const currentLateUntil =
      deadlineLateUntilRef.current?.value ?? deadlineLateUntil;

    if (!currentDueAt) {
      return "Due date is required.";
    }
    if (currentLateUntil && !currentAllowLate) {
      return "Enable late submissions before setting a late deadline.";
    }
    if (
      currentDueAt &&
      currentLateUntil &&
      new Date(currentLateUntil) <= new Date(currentDueAt)
    ) {
      return "Late submission deadline must be after the due date.";
    }
    return "";
  }

  async function handleExtendDeadline() {
    const validationError = validateDeadlineForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsMutating(true);
    setError("");
    setSuccess("");
    const currentDueAt = deadlineDueAtRef.current?.value ?? deadlineDueAt;
    const currentAllowLate =
      deadlineAllowLateRef.current?.checked ?? deadlineAllowLate;
    const currentLateUntil =
      deadlineLateUntilRef.current?.value ?? deadlineLateUntil;
    try {
      const updated = await extendAssignmentDeadline(params.id, {
        due_at: new Date(currentDueAt).toISOString(),
        allow_late_submissions: currentAllowLate,
        late_submission_deadline: currentLateUntil
          ? new Date(currentLateUntil).toISOString()
          : null
      });
      setAssignment(updated);
      setSuccess("Assignment deadline extended.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to extend deadline.");
    } finally {
      setIsMutating(false);
    }
  }

  async function handleReopen() {
    const validationError = validateDeadlineForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsMutating(true);
    setError("");
    setSuccess("");
    const currentDueAt = deadlineDueAtRef.current?.value ?? deadlineDueAt;
    const currentAllowLate =
      deadlineAllowLateRef.current?.checked ?? deadlineAllowLate;
    const currentLateUntil =
      deadlineLateUntilRef.current?.value ?? deadlineLateUntil;
    try {
      const updated = await reopenAssignment(params.id, {
        due_at: new Date(currentDueAt).toISOString(),
        allow_late_submissions: currentAllowLate,
        late_submission_deadline: currentLateUntil
          ? new Date(currentLateUntil).toISOString()
          : null
      });
      setAssignment(updated);
      setSuccess("Assignment reopened.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to reopen assignment.");
    } finally {
      setIsMutating(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading assignment..." />;
  }

  if (error && !assignment) {
    return <EmptyState title="Assignment unavailable" description={error} />;
  }

  if (!assignment) {
    return (
      <EmptyState
        title="Assignment not found"
        description="The assignment could not be found or you do not have access."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={assignment.title}
        description={`${assignment.class_arm_name} · ${assignment.subject_name} · ${assignment.topic_title}`}
        actions={
          <Link href="/teacher/assignments">
            <Button variant="secondary">Back to Assignments</Button>
          </Link>
        }
      />

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
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="grid gap-3 text-sm text-muted sm:grid-cols-2 lg:grid-cols-3">
            <p>
              <span className="block font-semibold text-ink">Status</span>
              <span className="mt-1 inline-block">
                <Badge
                  tone={statusTone[assignment.status]}
                  data-testid="assignment-status-badge"
                >
                  {assignment.status}
                </Badge>
              </span>
            </p>
            <p>
              <span className="block font-semibold text-ink">Questions</span>
              {assignment.question_count}
            </p>
            <p>
              <span className="block font-semibold text-ink">Duration</span>
              {assignment.duration_minutes
                ? `${assignment.duration_minutes} minutes`
                : "Not timed"}
            </p>
            <p>
              <span className="block font-semibold text-ink">Starts</span>
              {formatDate(assignment.starts_at)}
            </p>
            <p>
              <span className="block font-semibold text-ink">Due</span>
              {formatDate(assignment.due_at)}
            </p>
            <p>
              <span className="block font-semibold text-ink">Deadline status</span>
              <span className="mt-1 inline-block">
                <Badge
                  tone={deadlineStatusTone(assignment.deadline_status)}
                  data-testid="assignment-deadline-status-badge"
                >
                  {formatDeadlineStatus(assignment.deadline_status)}
                </Badge>
              </span>
            </p>
            <p>
              <span className="block font-semibold text-ink">Late submissions</span>
              {assignment.allow_late_submissions ? "Allowed" : "Not allowed"}
            </p>
            <p>
              <span className="block font-semibold text-ink">Late deadline</span>
              {formatDate(assignment.late_submission_deadline)}
            </p>
            <p>
              <span className="block font-semibold text-ink">Original due</span>
              {formatDate(assignment.original_due_at)}
            </p>
            <p>
              <span className="block font-semibold text-ink">Late submissions</span>
              {assignment.late_submission_count ?? 0}
            </p>
            <p>
              <span className="block font-semibold text-ink">Published</span>
              {formatDate(assignment.published_at)}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {assignment.status === "draft" ? (
              <Button
                isLoading={isMutating}
                onClick={() => runAction(publishAssignment, "Assignment published.")}
              >
                Publish
              </Button>
            ) : null}
            {assignment.status === "published" ? (
              <Button
                variant="secondary"
                isLoading={isMutating}
                onClick={() => runAction(closeAssignment, "Assignment closed.")}
              >
                Close
              </Button>
            ) : null}
            {["draft", "closed"].includes(assignment.status) ? (
              <Button
                variant="ghost"
                isLoading={isMutating}
                onClick={() => runAction(archiveAssignment, "Assignment archived.")}
              >
                Archive
              </Button>
            ) : null}
            {["published", "closed"].includes(assignment.status) ? (
              <Button
                variant="secondary"
                onClick={() =>
                  router.push(`/teacher/assignments/${assignment.id}/results`)
                }
              >
                View Results
              </Button>
            ) : null}
          </div>
        </div>
        {assignment.instructions ? (
          <p className="mt-5 rounded-md bg-surface p-3 text-sm leading-6 text-muted">
            {assignment.instructions}
          </p>
        ) : null}
      </Card>

      {assignment.status !== "archived" ? (
        <Card className="mt-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-ink">
                Deadline Management
              </h2>
              <p className="mt-1 text-sm leading-6 text-muted">
                Extend due dates or reopen a closed assignment. Students are
                notified when the deadline changes.
              </p>
            </div>
          </div>
          <div
            className="mt-4 grid gap-4 md:grid-cols-2"
            data-testid="assignment-extend-deadline-form"
          >
            <Input
              label="New due date"
              type="datetime-local"
              data-testid="assignment-due-at-input"
              ref={deadlineDueAtRef}
              value={deadlineDueAt}
              onChange={(event) => setDeadlineDueAt(event.target.value)}
            />
            <Input
              label="Late submission deadline"
              type="datetime-local"
              data-testid="assignment-late-deadline-input"
              ref={deadlineLateUntilRef}
              disabled={!deadlineAllowLate}
              value={deadlineLateUntil}
              onChange={(event) => setDeadlineLateUntil(event.target.value)}
            />
          </div>
          <label className="mt-4 flex items-start gap-3 rounded-md border border-line bg-surface px-3 py-3 text-sm text-muted">
            <input
              type="checkbox"
              data-testid="assignment-allow-late-checkbox"
              ref={deadlineAllowLateRef}
              className="mt-1"
              checked={deadlineAllowLate}
              onChange={(event) => {
                setDeadlineAllowLate(event.target.checked);
                if (!event.target.checked) {
                  setDeadlineLateUntil("");
                }
              }}
            />
            <span>
              <span className="block font-semibold text-ink">
                Allow late submissions
              </span>
              Late submissions stay open until the late deadline, if one is set.
            </span>
          </label>
          <div className="mt-4 flex flex-wrap gap-2">
            {assignment.status === "published" ? (
              <Button
                variant="secondary"
                isLoading={isMutating}
                data-testid="assignment-extend-deadline-button"
                onClick={handleExtendDeadline}
              >
                Extend Deadline
              </Button>
            ) : null}
            {assignment.status === "closed" ? (
              <Button
                isLoading={isMutating}
                data-testid="assignment-reopen-button"
                onClick={handleReopen}
              >
                Reopen Assignment
              </Button>
            ) : null}
          </div>
        </Card>
      ) : null}

      <section className="mt-6 space-y-3">
        <h2 className="text-lg font-semibold text-ink">Questions</h2>
        {assignment.assignment_questions.map((item) => (
          <Card key={item.id}>
            <p className="text-sm font-semibold text-brand-700">
              Question {item.order} · {item.marks} mark{item.marks === 1 ? "" : "s"}
            </p>
            <p className="mt-2 text-base font-medium leading-7 text-ink">
              {item.question_detail?.question_text ?? `Question #${item.question}`}
            </p>
            <p className="mt-2 text-sm text-muted">
              Difficulty: {item.question_detail?.difficulty ?? "Not set"}
            </p>
          </Card>
        ))}
      </section>
    </>
  );
}
