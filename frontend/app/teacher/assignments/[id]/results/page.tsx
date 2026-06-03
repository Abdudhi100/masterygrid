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
import { getTeacherAssignmentResults } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type {
  MostMissedQuestion,
  QuestionPerformanceRow,
  StudentResultRow,
  TeacherAssignmentResults
} from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function formatDate(value?: string | null, emptyLabel = "Not set") {
  if (!value) {
    return emptyLabel;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return emptyLabel;
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatDuration(seconds: number | null) {
  if (seconds === null) {
    return "Not recorded";
  }

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  return `${remainingSeconds}s`;
}

function formatPercentage(value: number) {
  return `${Number(value).toFixed(2)}%`;
}

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

function assignmentStatusTone(status: string): BadgeTone {
  if (
    status === "published" ||
    status === "graded" ||
    status === "submitted" ||
    status === "auto_submitted"
  ) {
    return "success";
  }

  if (status === "draft" || status === "in_progress") {
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

function BackToAssignmentsButton() {
  return (
    <Link href="/teacher/assignments">
      <Button variant="secondary">Back to Assignments</Button>
    </Link>
  );
}

export default function AssignmentResultsPage({
  params
}: {
  params: { id: string };
}) {
  const [results, setResults] = useState<TeacherAssignmentResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadResults = useCallback(async () => {
    setError("");
    try {
      setResults(await getTeacherAssignmentResults(params.id));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load assignment results."
      );
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadResults();
  }, [loadResults]);

  if (isLoading) {
    return (
      <>
        <PageHeader title="Assignment Results" actions={<BackToAssignmentsButton />} />
        <LoadingState label="Loading assignment results..." />
      </>
    );
  }

  if (error) {
    return (
      <>
        <PageHeader title="Assignment Results" actions={<BackToAssignmentsButton />} />
        <EmptyState title="Results unavailable" description={error} />
      </>
    );
  }

  if (!results) {
    return (
      <>
        <PageHeader title="Assignment Results" actions={<BackToAssignmentsButton />} />
        <EmptyState
          title="No results found"
          description="This assignment result could not be loaded."
        />
      </>
    );
  }

  const { assignment, submission_summary: summary } = results;
  const hasSubmissions =
    summary.total_started > 0 ||
    summary.total_submitted > 0 ||
    summary.total_graded > 0;
  const mostMissedQuestions = results.most_missed_questions.filter(
    (question) => question.wrong_count > 0
  );

  return (
    <>
      <PageHeader
        title="Assignment Results"
        description="Review student scores, submission coverage, and question-level performance."
        actions={<BackToAssignmentsButton />}
      />

      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold text-ink">{assignment.title}</h2>
              <Badge tone={assignmentStatusTone(assignment.status)}>
                {formatStatus(assignment.status)}
              </Badge>
            </div>
            <dl className="mt-4 grid gap-4 text-sm text-muted sm:grid-cols-2 lg:grid-cols-5">
              <div>
                <dt className="font-semibold text-ink">Subject</dt>
                <dd className="mt-1">{assignment.subject}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Topic</dt>
                <dd className="mt-1">{assignment.topic}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Class arm</dt>
                <dd className="mt-1">{assignment.class_arm}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Questions</dt>
                <dd className="mt-1">{assignment.question_count}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Due date</dt>
                <dd className="mt-1">{formatDate(assignment.due_at)}</dd>
              </div>
            </dl>
          </div>
        </div>
      </Card>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatCard
          label="Expected students"
          value={summary.total_students_expected}
        />
        <StatCard label="Started" value={summary.total_started} />
        <StatCard label="Submitted" value={summary.total_submitted} />
        <StatCard label="Graded" value={summary.total_graded} />
        <StatCard label="Late" value={summary.total_late} />
        <StatCard label="Not started" value={summary.total_not_started} />
        <StatCard
          label="Submission rate"
          value={formatPercentage(summary.submission_rate)}
        />
        <StatCard
          label="Average score"
          value={formatPercentage(summary.average_percentage)}
        />
        <StatCard
          label="Highest score"
          value={formatPercentage(summary.highest_percentage)}
        />
        <StatCard
          label="Lowest score"
          value={formatPercentage(summary.lowest_percentage)}
        />
      </section>

      {!hasSubmissions ? (
        <section className="mt-6">
          <EmptyState
            title="No submissions yet"
            description="Student performance will appear here once learners start or submit this assignment."
          />
        </section>
      ) : (
        <>
          <section
            className="mt-6 space-y-3"
            data-testid="teacher-assignment-results-table"
          >
            <h2 className="text-lg font-semibold text-ink">Student Results</h2>
            <DataTable<StudentResultRow>
              data={results.student_results}
              emptyTitle="No student results"
              emptyDescription="No enrolled students or submissions were found for this assignment."
              columns={[
                {
                  key: "student_name",
                  header: "Student name",
                  render: (row) => (
                    <span
                      className="font-semibold"
                      data-testid="teacher-assignment-student-result-row"
                    >
                      {row.student_name}
                    </span>
                  )
                },
                {
                  key: "admission_number",
                  header: "Admission number",
                  render: (row) => row.admission_number ?? "Not set"
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => (
                    <Badge tone={assignmentStatusTone(row.status)}>
                      {formatStatus(row.status)}
                    </Badge>
                  )
                },
                {
                  key: "score",
                  header: "Score",
                  render: (row) =>
                    row.total_marks > 0
                      ? `${row.score}/${row.total_marks}`
                      : "Not graded"
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
                  key: "submitted_at",
                  header: "Submitted at",
                  render: (row) => formatDate(row.submitted_at, "Not submitted")
                },
                {
                  key: "is_late",
                  header: "Late",
                  render: (row) =>
                    row.is_late ? (
                      <Badge tone="warning" data-testid="submission-late-badge">
                        Late
                      </Badge>
                    ) : (
                      <Badge tone="neutral">On time</Badge>
                    )
                },
                {
                  key: "time_spent_seconds",
                  header: "Time spent",
                  render: (row) => formatDuration(row.time_spent_seconds)
                }
              ]}
            />
          </section>

          <section className="mt-6 space-y-3">
            <h2 className="text-lg font-semibold text-ink">
              Question Performance
            </h2>
            <DataTable<QuestionPerformanceRow>
              data={results.question_performance}
              emptyTitle="No question performance"
              emptyDescription="Question-level performance appears after graded submissions exist."
              columns={[
                {
                  key: "question_text",
                  header: "Question text",
                  render: (row) => (
                    <span className="block min-w-[20rem] max-w-2xl leading-6">
                      {row.question_text}
                    </span>
                  )
                },
                {
                  key: "total_attempts",
                  header: "Total attempts"
                },
                {
                  key: "correct_count",
                  header: "Correct"
                },
                {
                  key: "wrong_count",
                  header: "Wrong"
                },
                {
                  key: "correct_percentage",
                  header: "Correct percentage",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.correct_percentage)}</span>
                      <ScoreBadge percentage={row.correct_percentage} />
                    </div>
                  )
                }
              ]}
            />
          </section>

          <section className="mt-6 space-y-3">
            <h2 className="text-lg font-semibold text-ink">
              Most Missed Questions
            </h2>
            <DataTable<MostMissedQuestion>
              data={mostMissedQuestions}
              emptyTitle="No missed questions"
              emptyDescription="No wrong answers have been recorded for this assignment yet."
              columns={[
                {
                  key: "question_text",
                  header: "Question text",
                  render: (row) => (
                    <span className="block min-w-[20rem] max-w-2xl leading-6">
                      {row.question_text}
                    </span>
                  )
                },
                {
                  key: "wrong_count",
                  header: "Wrong count"
                },
                {
                  key: "correct_percentage",
                  header: "Correct percentage",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.correct_percentage)}</span>
                      <ScoreBadge percentage={row.correct_percentage} />
                    </div>
                  )
                }
              ]}
            />
          </section>
        </>
      )}
    </>
  );
}
