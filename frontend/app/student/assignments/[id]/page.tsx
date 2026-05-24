"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getMyAssignments, startAssignment } from "@/lib/submissions";
import type { StudentAssignmentItem } from "@/types/submissions";

function isCompleted(assignment: StudentAssignmentItem) {
  return ["submitted", "graded", "auto_submitted"].includes(
    assignment.submission_status ?? ""
  );
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export default function StudentAssignmentDetailPage({
  params
}: {
  params: { id: string };
}) {
  const [assignments, setAssignments] = useState<StudentAssignmentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAssignments() {
      try {
        setAssignments(await getMyAssignments());
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load assignment.");
      } finally {
        setIsLoading(false);
      }
    }
    void loadAssignments();
  }, []);

  const assignment = useMemo(
    () => assignments.find((item) => String(item.id) === params.id) ?? null,
    [assignments, params.id]
  );

  async function handleStart() {
    setIsStarting(true);
    setError("");
    try {
      const submission = await startAssignment(params.id);
      window.location.href = `/student/assignments/${params.id}/attempt?submissionId=${submission.id}`;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to start assignment.");
    } finally {
      setIsStarting(false);
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
        description="This assignment is not available to your account."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={assignment.title}
        description={`${assignment.subject_name} · ${assignment.topic_title} · ${assignment.class_arm_name}`}
        actions={
          <Link href="/student/assignments">
            <Button variant="secondary">Back to My Assignments</Button>
          </Link>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card>
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="grid gap-3 text-sm text-muted sm:grid-cols-2">
            <p>
              <span className="block font-semibold text-ink">Status</span>
              <span className="mt-1 inline-block">
                <Badge tone={isCompleted(assignment) ? "success" : "brand"}>
                  {assignment.submission_status ?? "pending"}
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
                : "No timer"}
            </p>
            <p>
              <span className="block font-semibold text-ink">Due date</span>
              {formatDate(assignment.due_at)}
            </p>
          </div>
          <div>
            {isCompleted(assignment) && assignment.submission_id ? (
              <Link
                href={`/student/assignments/${assignment.id}/result?submissionId=${assignment.submission_id}`}
              >
                <Button>View Result</Button>
              </Link>
            ) : assignment.submission_status === "in_progress" &&
              assignment.submission_id ? (
              <Link
                href={`/student/assignments/${assignment.id}/attempt?submissionId=${assignment.submission_id}`}
              >
                <Button>Continue Assignment</Button>
              </Link>
            ) : (
              <Button
                onClick={handleStart}
                isLoading={isStarting}
                data-testid="assignment-start-button"
              >
                Start Assignment
              </Button>
            )}
          </div>
        </div>
        {assignment.instructions ? (
          <p className="mt-5 rounded-md bg-surface p-3 text-sm leading-6 text-muted">
            {assignment.instructions}
          </p>
        ) : null}
      </Card>
    </>
  );
}
