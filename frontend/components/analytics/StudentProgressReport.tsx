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
import { ApiError } from "@/lib/api";
import { getStudentProgressReport } from "@/lib/analytics";
import type {
  StudentProgressAssignmentResult,
  StudentProgressMissedAssignment,
  StudentProgressPracticeSession,
  StudentProgressRecommendation,
  StudentProgressReport as StudentProgressReportType,
  StudentProgressRiskLevel,
  StudentProgressSubjectBreakdown,
  StudentProgressTopic,
  StudentProgressTopicBreakdown
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

function formatPercentage(value?: number | null) {
  if (value === null || value === undefined) {
    return "0.00%";
  }
  return `${Number(value).toFixed(2)}%`;
}

function riskTone(risk: StudentProgressRiskLevel): BadgeTone {
  if (risk === "critical" || risk === "high") {
    return "danger";
  }
  if (risk === "moderate") {
    return "warning";
  }
  return "success";
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

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function ScoreBadge({ percentage }: { percentage: number }) {
  const label =
    percentage >= 70 ? "strong" : percentage >= 50 ? "average" : "weak";
  return <Badge tone={scoreTone(percentage)}>{label}</Badge>;
}

function RiskBadge({ risk }: { risk: StudentProgressRiskLevel }) {
  return (
    <Badge tone={riskTone(risk)} data-testid="student-progress-risk-badge">
      {titleCase(risk)}
    </Badge>
  );
}

function RecommendationCard({
  recommendation,
  baseRole
}: {
  recommendation: StudentProgressRecommendation;
  baseRole: "admin" | "teacher";
}) {
  const href =
    baseRole === "teacher" && typeof recommendation.action_payload.href === "string"
      ? recommendation.action_payload.href
      : "";

  return (
    <div className="rounded-md border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        {recommendation.topic_title ? (
          <Badge tone="warning">{recommendation.topic_title}</Badge>
        ) : null}
        {recommendation.subject_name ? (
          <Badge tone="neutral">{recommendation.subject_name}</Badge>
        ) : null}
      </div>
      <h3 className="mt-3 font-semibold text-ink">
        {recommendation.recommended_action}
      </h3>
      <p className="mt-2 text-sm leading-6 text-muted">
        {recommendation.reason}
      </p>
      {href ? (
        <Link href={href} className="mt-4 inline-block">
          <Button variant="secondary">Create Remedial Assignment</Button>
        </Link>
      ) : null}
    </div>
  );
}

export function StudentProgressReport({
  studentId,
  baseRole,
  backHref,
  backLabel,
  printHref
}: {
  studentId: string;
  baseRole: "admin" | "teacher";
  backHref: string;
  backLabel: string;
  printHref: string;
}) {
  const [report, setReport] = useState<StudentProgressReportType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReport = useCallback(async () => {
    try {
      setReport(await getStudentProgressReport(studentId));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load student progress report."
      );
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  if (isLoading) {
    return <LoadingState label="Loading student progress report..." />;
  }

  if (error) {
    return <EmptyState title="Progress report unavailable" description={error} />;
  }

  if (!report) {
    return (
      <EmptyState
        title="No progress report"
        description="This student progress report could not be loaded."
      />
    );
  }

  return (
    <div data-testid="student-progress-report-page">
      <PageHeader
        title={`${report.student.full_name} Progress Report`}
        description="Internal academic report for assignments, practice, weak topics, and next steps."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href={printHref} data-testid="student-progress-print-link">
              <Button variant="secondary">Print / Export</Button>
            </Link>
            <Link href={backHref}>
              <Button variant="secondary">{backLabel}</Button>
            </Link>
          </div>
        }
      />

      <Card data-testid="student-progress-identity-card">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge risk={report.summary.risk_level} />
              <Badge tone="brand">Generated {formatDate(report.generated_at)}</Badge>
            </div>
            <h2 className="mt-3 text-xl font-semibold text-ink">
              {report.student.full_name}
            </h2>
            <dl className="mt-4 grid gap-3 text-sm text-muted sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="font-semibold text-ink">Email</dt>
                <dd className="mt-1 break-words">{report.student.email}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Admission number</dt>
                <dd className="mt-1">
                  {report.student.admission_number ?? "Not set"}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Class arm</dt>
                <dd className="mt-1">{report.student.class_arm ?? "Not set"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">School</dt>
                <dd className="mt-1">{report.student.school ?? "Not set"}</dd>
              </div>
            </dl>
          </div>
          <div className="rounded-md border border-line bg-surface p-4">
            <p className="text-sm font-semibold text-ink">
              {report.learning_path_summary.headline}
            </p>
            <p className="mt-2 max-w-md text-sm leading-6 text-muted">
              {report.learning_path_summary.message}
            </p>
          </div>
        </div>
      </Card>

      <section
        className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        data-testid="student-progress-summary"
      >
        <StatCard
          label="Overall average"
          value={formatPercentage(report.summary.overall_average)}
        />
        <StatCard
          label="Assignment average"
          value={formatPercentage(report.summary.assignment_average)}
        />
        <StatCard
          label="Practice average"
          value={formatPercentage(report.summary.practice_average)}
        />
        <StatCard
          label="Graded assignments"
          value={report.summary.graded_assignments_count}
        />
        <StatCard
          label="Missed assignments"
          value={report.summary.missed_assignments_count}
        />
        <StatCard
          label="Practice sessions"
          value={report.summary.practice_sessions_count}
        />
        <StatCard label="Weak topics" value={report.summary.weak_topic_count} />
        <StatCard label="Strong topics" value={report.summary.strong_topic_count} />
      </section>

      <section className="mt-6 space-y-6">
        <Card data-testid="student-progress-recommendations">
          <h2 className="text-base font-semibold text-ink">Recommended Next Steps</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            These actions are computed from assignment and practice performance.
          </p>
          {report.recommendations.length ? (
            <div className="mt-5 grid gap-4 xl:grid-cols-2">
              {report.recommendations.map((recommendation, index) => (
                <RecommendationCard
                  key={`${recommendation.topic_id ?? "missed"}-${index}`}
                  recommendation={recommendation}
                  baseRole={baseRole}
                />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No recommendations yet"
                description="Recommendations will appear after graded work or practice sessions exist."
              />
            </div>
          )}
        </Card>

        <Card data-testid="student-assignment-performance">
          <h2 className="text-base font-semibold text-ink">
            Assignment Performance
          </h2>
          <div className="mt-5 space-y-6">
            <DataTable<StudentProgressAssignmentResult>
              data={report.assignment_performance.recent_results}
              emptyTitle="No assignment results"
              emptyDescription="Graded assignment results will appear here."
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
                { key: "subject_name", header: "Subject" },
                { key: "topic_title", header: "Topic" },
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
                  header: "Graded",
                  render: (row) => formatDate(row.graded_at)
                }
              ]}
            />

            <div className="grid gap-6 xl:grid-cols-2">
              <DataTable<StudentProgressSubjectBreakdown>
                data={report.assignment_performance.subject_breakdown}
                emptyTitle="No assignment subject breakdown"
                emptyDescription="Subject breakdown appears after graded assignments."
                columns={[
                  { key: "subject_name", header: "Subject" },
                  {
                    key: "average_percentage",
                    header: "Average",
                    render: (row) => formatPercentage(row.average_percentage)
                  },
                  {
                    key: "graded_assignments_count",
                    header: "Graded",
                    render: (row) => row.graded_assignments_count ?? 0
                  }
                ]}
              />

              <DataTable<StudentProgressMissedAssignment>
                data={report.assignment_performance.missed_assignments}
                emptyTitle="No missed assignments"
                emptyDescription="No missed assignments are currently recorded."
                columns={[
                  {
                    key: "title",
                    header: "Missed assignment",
                    render: (row) => (
                      <span className="block min-w-[14rem] font-semibold">
                        {row.title}
                      </span>
                    )
                  },
                  { key: "subject", header: "Subject" },
                  { key: "topic", header: "Topic" },
                  {
                    key: "due_at",
                    header: "Due date",
                    render: (row) => formatDate(row.due_at)
                  }
                ]}
              />
            </div>
          </div>
        </Card>

        <Card data-testid="student-practice-performance">
          <h2 className="text-base font-semibold text-ink">Practice Performance</h2>
          <div className="mt-5 space-y-6">
            <DataTable<StudentProgressPracticeSession>
              data={report.practice_performance.recent_sessions}
              emptyTitle="No practice sessions"
              emptyDescription="Submitted practice sessions will appear here."
              columns={[
                { key: "subject_name", header: "Subject" },
                {
                  key: "topic_title",
                  header: "Topic",
                  render: (row) => row.topic_title ?? "Mixed topic"
                },
                { key: "difficulty", header: "Difficulty" },
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
                  key: "submitted_at",
                  header: "Submitted",
                  render: (row) => formatDate(row.submitted_at)
                }
              ]}
            />

            <div className="grid gap-6 xl:grid-cols-2">
              <DataTable<StudentProgressSubjectBreakdown>
                data={report.practice_performance.subject_breakdown}
                emptyTitle="No practice subject breakdown"
                emptyDescription="Subject breakdown appears after practice sessions."
                columns={[
                  { key: "subject_name", header: "Subject" },
                  {
                    key: "average_percentage",
                    header: "Average",
                    render: (row) => formatPercentage(row.average_percentage)
                  },
                  {
                    key: "sessions_completed",
                    header: "Sessions",
                    render: (row) => row.sessions_completed ?? 0
                  }
                ]}
              />

              <DataTable<StudentProgressTopicBreakdown>
                data={report.practice_performance.topic_breakdown}
                emptyTitle="No practice topic breakdown"
                emptyDescription="Topic breakdown appears after topic-specific practice."
                columns={[
                  { key: "topic_title", header: "Topic" },
                  {
                    key: "average_percentage",
                    header: "Average",
                    render: (row) => formatPercentage(row.average_percentage)
                  },
                  {
                    key: "questions_answered",
                    header: "Answered",
                    render: (row) => row.questions_answered ?? 0
                  }
                ]}
              />
            </div>
          </div>
        </Card>

        <section className="grid gap-6 xl:grid-cols-2">
          <Card data-testid="student-weak-topics">
            <h2 className="text-base font-semibold text-ink">Weak Topics</h2>
            <div className="mt-4">
              <DataTable<StudentProgressTopic>
                data={report.weak_topics}
                emptyTitle="No weak topics"
                emptyDescription="No weak topics have been detected yet."
                columns={[
                  { key: "subject_name", header: "Subject" },
                  { key: "topic_title", header: "Topic" },
                  {
                    key: "average_percentage",
                    header: "Average",
                    render: (row) => formatPercentage(row.average_percentage)
                  },
                  { key: "evidence_count", header: "Evidence" }
                ]}
              />
            </div>
          </Card>

          <Card data-testid="student-strong-topics">
            <h2 className="text-base font-semibold text-ink">Strong Topics</h2>
            <div className="mt-4">
              <DataTable<StudentProgressTopic>
                data={report.strong_topics}
                emptyTitle="No strong topics yet"
                emptyDescription="Strong topics will appear as performance improves."
                columns={[
                  { key: "subject_name", header: "Subject" },
                  { key: "topic_title", header: "Topic" },
                  {
                    key: "average_percentage",
                    header: "Average",
                    render: (row) => formatPercentage(row.average_percentage)
                  },
                  { key: "evidence_count", header: "Evidence" }
                ]}
              />
            </div>
          </Card>
        </section>
      </section>
    </div>
  );
}
