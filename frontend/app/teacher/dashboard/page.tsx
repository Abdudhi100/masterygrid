"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getTeacherOverview } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { TeacherOverview } from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatPercentage(value: number) {
  return `${Number(value).toFixed(2)}%`;
}

function statusTone(status: string): BadgeTone {
  if (status === "published") {
    return "success";
  }

  if (status === "draft") {
    return "warning";
  }

  if (status === "archived") {
    return "danger";
  }

  return "neutral";
}

function scoreTone(percentage: number): BadgeTone {
  if (percentage >= 70) {
    return "success";
  }

  if (percentage >= 50) {
    return "warning";
  }

  return "danger";
}

const dashboardLinks = [
  {
    title: "Assignments",
    description: "Create, publish, close, and archive assignments.",
    href: "/teacher/assignments",
    action: "Open Assignments"
  },
  {
    title: "Results",
    description: "Review assignment-level results and class performance.",
    href: "/teacher/results",
    action: "Open Results"
  },
  {
    title: "Weak Students",
    description: "Find learners who need targeted support.",
    href: "/teacher/weak-students",
    action: "View Students"
  },
  {
    title: "Weak Topics",
    description: "Find topics that need reteaching or reinforcement.",
    href: "/teacher/weak-topics",
    action: "View Topics"
  }
];

export default function TeacherDashboardPage() {
  const [overview, setOverview] = useState<TeacherOverview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadOverview() {
      try {
        setOverview(await getTeacherOverview());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load teacher dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadOverview();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading teacher analytics..." />;
  }

  if (error) {
    return <EmptyState title="Dashboard unavailable" description={error} />;
  }

  if (!overview) {
    return (
      <EmptyState
        title="No dashboard data"
        description="Your assignment analytics will appear here once students submit work."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Teacher dashboard"
        description="Track assignments, submissions, grading coverage, and weak topic signals."
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label="Assignments"
          value={overview.total_assignments_created}
        />
        <StatCard label="Published" value={overview.published_assignments} />
        <StatCard label="Submissions" value={overview.total_submissions} />
        <StatCard label="Graded" value={overview.graded_submissions} />
        <StatCard
          label="Average score"
          value={formatPercentage(overview.average_score_percentage)}
        />
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboardLinks.map((item) => (
          <Card key={item.href}>
            <h2 className="text-base font-semibold text-ink">{item.title}</h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-muted">
              {item.description}
            </p>
            <Link href={item.href} className="mt-4 inline-block">
              <Button variant="secondary">{item.action}</Button>
            </Link>
          </Card>
        ))}
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Recent Assignments
            </h2>
            <Link href="/teacher/assignments">
              <Button variant="ghost">View All</Button>
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {overview.recent_assignments.length ? (
              overview.recent_assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-semibold text-ink">{assignment.title}</p>
                      <p className="mt-1 text-sm text-muted">
                        {assignment.subject} - {assignment.class_arm}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        Due {formatDate(assignment.due_at)} -{" "}
                        {assignment.submission_count} submissions
                      </p>
                    </div>
                    <Badge tone={statusTone(assignment.status)}>
                      {assignment.status}
                    </Badge>
                  </div>
                  <Link
                    href={`/teacher/assignments/${assignment.id}/results`}
                    className="mt-3 inline-block"
                  >
                    <Button variant="secondary">View Results</Button>
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No recent assignments yet.</p>
            )}
          </div>
        </Card>

        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Recent Low-Performing Students
            </h2>
            <Link href="/teacher/weak-students">
              <Button variant="ghost">View All</Button>
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {overview.recent_low_performing_students.length ? (
              overview.recent_low_performing_students.map((student) => (
                <div
                  key={`${student.student_id}-${student.assignment_id}`}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-semibold text-ink">
                        {student.student_name}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        {student.assignment_title} - {student.topic}
                      </p>
                    </div>
                    <Badge tone={scoreTone(student.percentage)}>
                      {formatPercentage(student.percentage)}
                    </Badge>
                  </div>
                  <Link
                    href={`/teacher/students/${student.student_id}/performance`}
                    className="mt-3 inline-block"
                  >
                    <Button variant="secondary">View Performance</Button>
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">
                No low-performance alerts yet.
              </p>
            )}
          </div>
        </Card>
      </section>

      <section className="mt-6">
        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Weak Topics Summary
            </h2>
            <Link href="/teacher/weak-topics">
              <Button variant="ghost">View All</Button>
            </Link>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {overview.weak_topics_summary.length ? (
              overview.weak_topics_summary.map((topic) => (
                <div
                  key={`${topic.subject}-${topic.topic}-${topic.class_arm}`}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <p className="font-semibold text-ink">{topic.topic}</p>
                  <p className="mt-1 text-sm text-muted">
                    {topic.subject} - {topic.class_arm} -{" "}
                    {formatPercentage(topic.average_percentage)}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-muted">
                    {topic.recommendation}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No weak topics detected yet.</p>
            )}
          </div>
        </Card>
      </section>
    </>
  );
}
