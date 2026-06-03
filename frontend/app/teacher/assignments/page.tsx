"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Badge } from "@/components/ui/Badge";
import {
  archiveAssignment,
  closeAssignment,
  getAssignments,
  publishAssignment
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

export default function TeacherAssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadAssignments() {
    setError("");
    try {
      setAssignments(await getAssignments());
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load assignments."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAssignments();
  }, []);

  async function runAction(
    assignment: Assignment,
    action: (id: number) => Promise<Assignment>,
    message: string
  ) {
    setIsMutating(assignment.id);
    setError("");
    setSuccess("");
    try {
      await action(assignment.id);
      setSuccess(message);
      await loadAssignments();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
    } finally {
      setIsMutating(null);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading assignments..." />;
  }

  if (error && !assignments.length) {
    return <EmptyState title="Assignments unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Assignments"
        description="Manage generated topic assignments and publish them to students."
        actions={
          <Link href="/teacher/assignments/new">
            <Button>Create Assignment</Button>
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

      {assignments.length ? (
        <div className="space-y-4">
          {assignments.map((assignment) => (
            <Card key={assignment.id}>
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-ink">
                      {assignment.title}
                    </h2>
                    <Badge tone={statusTone[assignment.status]}>
                      {assignment.status}
                    </Badge>
                    <Badge tone={deadlineStatusTone(assignment.deadline_status)}>
                      {formatDeadlineStatus(assignment.deadline_status)}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm font-medium text-muted">
                    {assignment.class_arm_name} · {assignment.subject_name} ·{" "}
                    {assignment.topic_title}
                  </p>
                  <p className="mt-2 text-sm text-muted">
                    {assignment.question_count} questions · Due{" "}
                    {formatDate(assignment.due_at)} · Created{" "}
                    {formatDate(assignment.created_at)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link href={`/teacher/assignments/${assignment.id}`}>
                    <Button variant="secondary">View</Button>
                  </Link>
                  {assignment.status === "draft" ? (
                    <Button
                      isLoading={isMutating === assignment.id}
                      onClick={() =>
                        runAction(
                          assignment,
                          publishAssignment,
                          "Assignment published."
                        )
                      }
                    >
                      Publish
                    </Button>
                  ) : null}
                  {assignment.status === "published" ? (
                    <Button
                      variant="secondary"
                      isLoading={isMutating === assignment.id}
                      onClick={() =>
                        runAction(assignment, closeAssignment, "Assignment closed.")
                      }
                    >
                      Close
                    </Button>
                  ) : null}
                  {["draft", "closed"].includes(assignment.status) ? (
                    <Button
                      variant="ghost"
                      isLoading={isMutating === assignment.id}
                      onClick={() =>
                        runAction(
                          assignment,
                          archiveAssignment,
                          "Assignment archived."
                        )
                      }
                    >
                      Archive
                    </Button>
                  ) : null}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No assignments yet"
          description="Generate your first assignment from a logged lesson or a topic."
        />
      )}
    </>
  );
}
