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
import {
  getPracticeAnalyticsDashboard,
  getPracticeSessions
} from "@/lib/practice";
import { getMyAssignments } from "@/lib/submissions";
import type {
  PracticeAnalyticsDashboard,
  PracticeRecommendation,
  PracticeSession
} from "@/types/practice";
import type { StudentAssignmentItem } from "@/types/submissions";

function isCompleted(assignment: StudentAssignmentItem) {
  return ["submitted", "graded", "auto_submitted"].includes(
    assignment.submission_status ?? ""
  );
}

function formatPercentage(value?: number | string | null) {
  if (value === null || value === undefined || value === "") {
    return "Not scored";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "Not scored";
  }

  return `${numeric.toFixed(2)}%`;
}

function recommendationHref(recommendation: PracticeRecommendation) {
  const params = new URLSearchParams({
    subject: String(recommendation.subject_id),
    topic: String(recommendation.topic_id),
    difficulty: recommendation.recommended_difficulty,
    question_count: String(recommendation.suggested_question_count)
  });
  return `/student/practice?${params.toString()}`;
}

export default function StudentDashboardPage() {
  const [assignments, setAssignments] = useState<StudentAssignmentItem[]>([]);
  const [practiceSessions, setPracticeSessions] = useState<PracticeSession[]>([]);
  const [practiceAnalytics, setPracticeAnalytics] =
    useState<PracticeAnalyticsDashboard | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [assignmentData, practiceData, analyticsData] = await Promise.all([
          getMyAssignments(),
          getPracticeSessions(),
          getPracticeAnalyticsDashboard()
        ]);
        setAssignments(assignmentData);
        setPracticeSessions(practiceData);
        setPracticeAnalytics(analyticsData);
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

  const topRecommendation = practiceAnalytics?.recommendations[0] ?? null;

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
            <Link href="/student/learning-path">
              <Button variant="secondary">Learning Path</Button>
            </Link>
            <Link href="/student/practice/analytics">
              <Button variant="secondary">Practice Analytics</Button>
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
        <StatCard
          label="Practice average"
          value={formatPercentage(
            practiceAnalytics?.summary.overall_average_percentage
          )}
        />
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink">
            Practice Analytics
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Track your weak topics, strong topics, and recent practice scores.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/student/practice/analytics">
              <Button>Open Analytics</Button>
            </Link>
            <Link href="/student/learning-path">
              <Button variant="secondary">Learning Path</Button>
            </Link>
            <Link href="/student/practice">
              <Button variant="secondary">Start Practice</Button>
            </Link>
          </div>
        </Card>

        <Card>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Recommended Next
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                Suggestions come from your practice history and approved
                question-bank availability.
              </p>
            </div>
            <Link href="/student/learning-path">
              <Button variant="secondary">View All</Button>
            </Link>
          </div>
          {topRecommendation ? (
            <div className="mt-4 rounded-md border border-line bg-surface p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold text-ink">
                  {topRecommendation.topic_title}
                </p>
                <Badge
                  tone={
                    topRecommendation.priority === "high"
                      ? "danger"
                      : topRecommendation.priority === "medium"
                        ? "warning"
                        : "success"
                  }
                >
                  {topRecommendation.priority}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-muted">
                {topRecommendation.subject_name}
              </p>
              <p className="mt-2 text-sm leading-6 text-muted">
                {topRecommendation.reason}
              </p>
              <Link
                href={recommendationHref(topRecommendation)}
                className="mt-3 inline-block"
              >
                <Button>Start Recommended Practice</Button>
              </Link>
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Complete a practice session to unlock personalized analytics.
            </p>
          )}
        </Card>
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
