"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import { getMyAssignments } from "@/lib/submissions";
import type { StudentAssignmentItem } from "@/types/submissions";

type Filter = "all" | "pending" | "in_progress" | "completed" | "overdue";

function isCompleted(assignment: StudentAssignmentItem) {
  return ["submitted", "graded", "auto_submitted"].includes(
    assignment.submission_status ?? ""
  );
}

function isOverdue(assignment: StudentAssignmentItem) {
  return Boolean(
    assignment.due_at &&
      new Date(assignment.due_at) < new Date() &&
      !isCompleted(assignment)
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

function statusTone(assignment: StudentAssignmentItem) {
  if (isCompleted(assignment)) {
    return "success";
  }
  if (assignment.submission_status === "in_progress") {
    return "warning";
  }
  if (isOverdue(assignment)) {
    return "danger";
  }
  return "brand";
}

export default function StudentAssignmentsPage() {
  const [assignments, setAssignments] = useState<StudentAssignmentItem[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAssignments() {
      try {
        setAssignments(await getMyAssignments());
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load assignments.");
      } finally {
        setIsLoading(false);
      }
    }
    void loadAssignments();
  }, []);

  const filteredAssignments = useMemo(
    () =>
      assignments.filter((assignment) => {
        if (filter === "pending") {
          return !assignment.submission_status && !isOverdue(assignment);
        }
        if (filter === "in_progress") {
          return assignment.submission_status === "in_progress";
        }
        if (filter === "completed") {
          return isCompleted(assignment);
        }
        if (filter === "overdue") {
          return isOverdue(assignment);
        }
        return true;
      }),
    [assignments, filter]
  );

  if (isLoading) {
    return <LoadingState label="Loading assignments..." />;
  }

  if (error) {
    return <EmptyState title="Assignments unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="My Assignments"
        description="Start, continue, and review your published assignments."
      />

      <Card className="mb-4">
        <Select
          label="Filter"
          value={filter}
          options={[
            { value: "all", label: "All assignments" },
            { value: "pending", label: "Pending" },
            { value: "in_progress", label: "In progress" },
            { value: "completed", label: "Completed" },
            { value: "overdue", label: "Overdue" }
          ]}
          onChange={(event) => setFilter(event.target.value as Filter)}
        />
      </Card>

      {filteredAssignments.length ? (
        <div className="space-y-4">
          {filteredAssignments.map((assignment) => (
            <Card key={assignment.id} data-testid="student-assignment-card">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-ink">
                      {assignment.title}
                    </h2>
                    <Badge tone={statusTone(assignment)}>
                      {isOverdue(assignment)
                        ? "overdue"
                        : assignment.submission_status ?? "pending"}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm font-medium text-muted">
                    {assignment.subject_name} · {assignment.topic_title} ·{" "}
                    {assignment.class_arm_name}
                  </p>
                  <p className="mt-2 text-sm text-muted">
                    {assignment.question_count} questions ·{" "}
                    {assignment.duration_minutes
                      ? `${assignment.duration_minutes} minutes`
                      : "No timer"}{" "}
                    · Due {formatDate(assignment.due_at)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link href={`/student/assignments/${assignment.id}`}>
                    <Button variant="secondary">View Details</Button>
                  </Link>
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
                    <Link href={`/student/assignments/${assignment.id}/attempt`}>
                      <Button>Start Assignment</Button>
                    </Link>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No assignments here"
          description="Assignments matching this filter will appear here."
        />
      )}
    </>
  );
}
