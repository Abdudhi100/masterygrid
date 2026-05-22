"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { ApiError } from "@/lib/api";
import { getMyAssignments } from "@/lib/submissions";
import type { StudentAssignmentItem } from "@/types/submissions";

function isCompleted(assignment: StudentAssignmentItem) {
  return ["submitted", "graded", "auto_submitted"].includes(
    assignment.submission_status ?? ""
  );
}

export default function StudentDashboardPage() {
  const [assignments, setAssignments] = useState<StudentAssignmentItem[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAssignments() {
      try {
        setAssignments(await getMyAssignments());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load student assignments."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAssignments();
  }, []);

  const counts = useMemo(() => {
    const inProgress = assignments.filter(
      (assignment) => assignment.submission_status === "in_progress"
    );
    const completed = assignments.filter(isCompleted);
    const pending = assignments.filter(
      (assignment) => !assignment.submission_status
    );
    return { pending, inProgress, completed };
  }, [assignments]);

  if (isLoading) {
    return <LoadingState label="Loading your assignments..." />;
  }

  if (error) {
    return <EmptyState title="Dashboard unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Student dashboard"
        description="See your published assignments and current completion status."
        actions={
          <Link href="/student/assignments">
            <Button>Open My Assignments</Button>
          </Link>
        }
      />

      <section className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Pending" value={counts.pending.length} />
        <StatCard label="In progress" value={counts.inProgress.length} />
        <StatCard label="Completed" value={counts.completed.length} />
      </section>

      <section className="mt-6">
        {assignments.length ? (
          <Card>
            <h2 className="text-base font-semibold text-ink">My assignments</h2>
            <div className="mt-4 space-y-3">
              {assignments.slice(0, 8).map((assignment) => (
                <div
                  key={assignment.id}
                  className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-semibold text-ink">{assignment.title}</p>
                    <p className="mt-1 text-sm text-muted">
                      {assignment.subject_name} · {assignment.topic_title} ·{" "}
                      {assignment.question_count} questions
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      tone={
                        isCompleted(assignment)
                          ? "success"
                          : assignment.submission_status === "in_progress"
                            ? "warning"
                            : "brand"
                      }
                    >
                      {assignment.submission_status ?? "pending"}
                    </Badge>
                    {isCompleted(assignment) && assignment.submission_id ? (
                      <Link
                        href={`/student/assignments/${assignment.id}/result?submissionId=${assignment.submission_id}`}
                      >
                        <Button variant="secondary">Result</Button>
                      </Link>
                    ) : assignment.submission_status === "in_progress" &&
                      assignment.submission_id ? (
                      <Link
                        href={`/student/assignments/${assignment.id}/attempt?submissionId=${assignment.submission_id}`}
                      >
                        <Button variant="secondary">Continue</Button>
                      </Link>
                    ) : (
                      <Link href={`/student/assignments/${assignment.id}`}>
                        <Button variant="secondary">Open</Button>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : (
          <EmptyState
            title="No assignments yet"
            description="Published assignments for your class will appear here."
          />
        )}
      </section>
    </>
  );
}
