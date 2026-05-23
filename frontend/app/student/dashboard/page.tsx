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
import { getPracticeSessions } from "@/lib/practice";
import { getMyAssignments } from "@/lib/submissions";
import type { PracticeSession } from "@/types/practice";
import type { StudentAssignmentItem } from "@/types/submissions";

function isCompleted(assignment: StudentAssignmentItem) {
  return ["submitted", "graded", "auto_submitted"].includes(
    assignment.submission_status ?? ""
  );
}

export default function StudentDashboardPage() {
  const [assignments, setAssignments] = useState<StudentAssignmentItem[]>([]);
  const [practiceSessions, setPracticeSessions] = useState<PracticeSession[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [assignmentData, practiceData] = await Promise.all([
          getMyAssignments(),
          getPracticeSessions()
        ]);
        setAssignments(assignmentData);
        setPracticeSessions(practiceData);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load student dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const counts = useMemo(() => {
    const inProgress = assignments.filter(
      (assignment) => assignment.submission_status === "in_progress"
    );
    const completed = assignments.filter(isCompleted);
    const pending = assignments.filter(
      (assignment) => !assignment.submission_status
    );
    const submittedPractice = practiceSessions.filter(
      (session) => session.status === "submitted"
    );
    return { pending, inProgress, completed, submittedPractice };
  }, [assignments, practiceSessions]);

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
        description="See your assignments, continue work, and start self-paced practice."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/student/assignments">
              <Button variant="secondary">Open My Assignments</Button>
            </Link>
            <Link href="/student/practice">
              <Button>Start Practice</Button>
            </Link>
          </div>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Pending" value={counts.pending.length} />
        <StatCard label="In progress" value={counts.inProgress.length} />
        <StatCard label="Completed" value={counts.completed.length} />
        <StatCard
          label="Practice done"
          value={counts.submittedPractice.length}
        />
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

      <section className="mt-6">
        {practiceSessions.length ? (
          <Card>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <h2 className="text-base font-semibold text-ink">Recent practice</h2>
              <Link href="/student/practice">
                <Button variant="secondary">Open Practice</Button>
              </Link>
            </div>
            <div className="mt-4 space-y-3">
              {practiceSessions.slice(0, 5).map((session) => (
                <div
                  key={session.id}
                  className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-semibold text-ink">{session.subject_name}</p>
                    <p className="mt-1 text-sm text-muted">
                      {session.topic_title ?? "Any topic"} -{" "}
                      {session.question_count_requested} questions
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      tone={session.status === "submitted" ? "success" : "warning"}
                    >
                      {session.status}
                    </Badge>
                    {session.status === "submitted" ? (
                      <Link href={`/student/practice/${session.id}/result`}>
                        <Button variant="secondary">Result</Button>
                      </Link>
                    ) : (
                      <Link href={`/student/practice/${session.id}`}>
                        <Button variant="secondary">Continue</Button>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}
      </section>
    </>
  );
}
