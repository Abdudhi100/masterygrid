"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  archiveAssignment,
  closeAssignment,
  getAssignment,
  publishAssignment
} from "@/lib/academics";
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

export default function AssignmentDetailPage({
  params
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
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
      setSuccess(message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
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
                <Badge tone={statusTone[assignment.status]}>
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
