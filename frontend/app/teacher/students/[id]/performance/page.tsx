"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getTeacherStudentPerformance } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type {
  StudentMissedAssignment,
  StudentPerformanceGroup,
  StudentRecentScore,
  StudentWeakTopic,
  TeacherStudentPerformance
} from "@/types/analytics";

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

function scoreTone(percentage: number): BadgeTone {
  if (percentage >= 70) {
    return "success";
  }

  if (percentage >= 50) {
    return "warning";
  }

  return "danger";
}

function scoreLabel(percentage: number) {
  if (percentage >= 70) {
    return "strong";
  }

  if (percentage >= 50) {
    return "average";
  }

  return "weak";
}

function ScoreBadge({ percentage }: { percentage: number }) {
  return <Badge tone={scoreTone(percentage)}>{scoreLabel(percentage)}</Badge>;
}

export default function TeacherStudentPerformancePage({
  params
}: {
  params: { id: string };
}) {
  const [performance, setPerformance] =
    useState<TeacherStudentPerformance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPerformance = useCallback(async () => {
    try {
      setPerformance(await getTeacherStudentPerformance(params.id));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load student performance."
      );
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadPerformance();
  }, [loadPerformance]);

  if (isLoading) {
    return <LoadingState label="Loading student performance..." />;
  }

  if (error) {
    return <EmptyState title="Student performance unavailable" description={error} />;
  }

  if (!performance) {
    return (
      <EmptyState
        title="No performance data"
        description="This student performance record could not be loaded."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={`${performance.student.name} Performance`}
        description={`${performance.student.class_arm ?? "Class not set"} - ${
          performance.student.admission_number ?? "Admission number not set"
        }`}
        actions={
          <Link href="/teacher/weak-students">
            <Button variant="secondary">Back to Weak Students</Button>
          </Link>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Average score"
          value={formatPercentage(performance.average_percentage)}
        />
        <StatCard
          label="Assignments attempted"
          value={performance.assignments_attempted}
        />
        <StatCard
          label="Missed assignments"
          value={performance.missed_assignments.length}
        />
        <StatCard label="Weak topics" value={performance.weak_topics.length} />
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink">Student Details</h2>
          <dl className="mt-4 grid gap-3 text-sm text-muted sm:grid-cols-2">
            <div>
              <dt className="font-semibold text-ink">Name</dt>
              <dd className="mt-1">{performance.student.name}</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Email</dt>
              <dd className="mt-1 break-words">{performance.student.email}</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Admission number</dt>
              <dd className="mt-1">
                {performance.student.admission_number ?? "Not set"}
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Class arm</dt>
              <dd className="mt-1">{performance.student.class_arm ?? "Not set"}</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">Recommendation</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            {performance.recommendation}
          </p>
        </Card>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-2">
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">
            Performance By Subject
          </h2>
          <DataTable<StudentPerformanceGroup>
            data={performance.performance_by_subject}
            emptyTitle="No subject performance"
            emptyDescription="Subject performance appears after graded submissions exist."
            columns={[
              {
                key: "subject",
                header: "Subject",
                render: (row) => row.subject ?? "Not set"
              },
              {
                key: "average_percentage",
                header: "Average",
                render: (row) => (
                  <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                    <span>{formatPercentage(row.average_percentage)}</span>
                    <ScoreBadge percentage={row.average_percentage} />
                  </div>
                )
              },
              {
                key: "graded_submission_count",
                header: "Graded"
              }
            ]}
          />
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">
            Performance By Topic
          </h2>
          <DataTable<StudentPerformanceGroup>
            data={performance.performance_by_topic}
            emptyTitle="No topic performance"
            emptyDescription="Topic performance appears after graded submissions exist."
            columns={[
              {
                key: "topic",
                header: "Topic",
                render: (row) => row.topic ?? "Not set"
              },
              {
                key: "average_percentage",
                header: "Average",
                render: (row) => (
                  <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                    <span>{formatPercentage(row.average_percentage)}</span>
                    <ScoreBadge percentage={row.average_percentage} />
                  </div>
                )
              },
              {
                key: "graded_submission_count",
                header: "Graded"
              }
            ]}
          />
        </div>
      </section>

      <section className="mt-6 space-y-3">
        <h2 className="text-lg font-semibold text-ink">Recent Scores</h2>
        <DataTable<StudentRecentScore>
          data={performance.recent_scores}
          emptyTitle="No recent scores"
          emptyDescription="Recent scores will appear after this student has graded submissions."
          columns={[
            {
              key: "assignment_title",
              header: "Assignment",
              render: (row) => (
                <span className="block min-w-[14rem] font-semibold">
                  {row.assignment_title}
                </span>
              )
            },
            {
              key: "subject",
              header: "Subject"
            },
            {
              key: "topic",
              header: "Topic"
            },
            {
              key: "score",
              header: "Score",
              render: (row) => `${row.score}/${row.total_marks}`
            },
            {
              key: "percentage",
              header: "Percentage",
              render: (row) => (
                <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                  <span>{formatPercentage(row.percentage)}</span>
                  <ScoreBadge percentage={row.percentage} />
                </div>
              )
            },
            {
              key: "graded_at",
              header: "Graded at",
              render: (row) => formatDate(row.graded_at)
            }
          ]}
        />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-2">
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Weak Topics</h2>
          <DataTable<StudentWeakTopic>
            data={performance.weak_topics}
            emptyTitle="No weak topics"
            emptyDescription="No weak topics have been detected for this student yet."
            columns={[
              {
                key: "subject",
                header: "Subject",
                render: (row) => row.subject ?? "Not set"
              },
              {
                key: "topic",
                header: "Topic"
              },
              {
                key: "average_percentage",
                header: "Average",
                render: (row) => (
                  <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                    <span>{formatPercentage(row.average_percentage)}</span>
                    <ScoreBadge percentage={row.average_percentage} />
                  </div>
                )
              },
              {
                key: "submission_count",
                header: "Submissions",
                render: (row) =>
                  row.submission_count ?? row.graded_submission_count ?? 0
              }
            ]}
          />
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">
            Missed Assignments
          </h2>
          <DataTable<StudentMissedAssignment>
            data={performance.missed_assignments}
            emptyTitle="No missed assignments"
            emptyDescription="This student has no missed assignments in your current assignment list."
            columns={[
              {
                key: "title",
                header: "Assignment",
                render: (row) => (
                  <span className="block min-w-[14rem] font-semibold">
                    {row.title}
                  </span>
                )
              },
              {
                key: "subject",
                header: "Subject"
              },
              {
                key: "topic",
                header: "Topic"
              },
              {
                key: "due_at",
                header: "Due date",
                render: (row) => formatDate(row.due_at)
              }
            ]}
          />
        </div>
      </section>
    </>
  );
}
