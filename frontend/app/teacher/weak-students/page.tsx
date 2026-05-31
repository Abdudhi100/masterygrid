"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getTeacherWeakStudents } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { TeacherWeakStudent } from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

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

function riskTone(riskLevel: string): BadgeTone {
  if (riskLevel === "high") {
    return "danger";
  }

  if (riskLevel === "medium") {
    return "warning";
  }

  if (riskLevel === "low") {
    return "success";
  }

  return "neutral";
}

export default function TeacherWeakStudentsPage() {
  const [students, setStudents] = useState<TeacherWeakStudent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWeakStudents() {
      try {
        setStudents(await getTeacherWeakStudents());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load weak students."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadWeakStudents();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading weak students..." />;
  }

  if (error) {
    return <EmptyState title="Weak students unavailable" description={error} />;
  }

  const highRiskCount = students.filter(
    (student) => student.risk_level === "high"
  ).length;
  const missedAssignmentCount = students.reduce(
    (total, student) => total + student.missed_assignment_count,
    0
  );

  return (
    <>
      <PageHeader
        title="Weak Students"
        description="Identify learners who may need remediation, follow-up, or closer monitoring."
      />

      {students.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Weak students" value={students.length} />
            <StatCard label="High risk" value={highRiskCount} />
            <StatCard label="Missed assignments" value={missedAssignmentCount} />
            <StatCard
              label="Lowest average"
              value={formatPercentage(
                Math.min(...students.map((student) => student.average_percentage))
              )}
            />
          </section>

          <section className="mt-6">
            <DataTable<TeacherWeakStudent>
              data={students}
              columns={[
                {
                  key: "student_name",
                  header: "Student name",
                  render: (row) => (
                    <span className="font-semibold">{row.student_name}</span>
                  )
                },
                {
                  key: "class_arm",
                  header: "Class arm",
                  render: (row) => row.class_arm ?? "Not set"
                },
                {
                  key: "average_percentage",
                  header: "Average",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.average_percentage)}</span>
                      <Badge tone={scoreTone(row.average_percentage)}>
                        {scoreLabel(row.average_percentage)}
                      </Badge>
                    </div>
                  )
                },
                {
                  key: "graded_submission_count",
                  header: "Graded"
                },
                {
                  key: "missed_assignment_count",
                  header: "Missed"
                },
                {
                  key: "weak_topics",
                  header: "Weak topics",
                  render: (row) =>
                    row.weak_topics.length ? (
                      <div className="min-w-[14rem] space-y-1">
                        {row.weak_topics.slice(0, 3).map((topic) => (
                          <p
                            key={`${topic.subject ?? "subject"}-${topic.topic}`}
                            className="text-sm text-ink"
                          >
                            {topic.topic} - {formatPercentage(topic.average_percentage)}
                          </p>
                        ))}
                        {row.weak_topics.length > 3 ? (
                          <p className="text-xs font-semibold text-muted">
                            +{row.weak_topics.length - 3} more
                          </p>
                        ) : null}
                      </div>
                    ) : (
                      "No weak topics listed"
                    )
                },
                {
                  key: "risk_level",
                  header: "Risk level",
                  render: (row) => (
                    <Badge tone={riskTone(row.risk_level)}>{row.risk_level}</Badge>
                  )
                },
                {
                  key: "recommendation",
                  header: "Recommendation",
                  render: (row) => (
                    <span className="block min-w-[18rem] max-w-lg leading-6">
                      {row.recommendation}
                    </span>
                  )
                },
                {
                  key: "action",
                  header: "Action",
                  render: (row) => (
                    <div className="flex min-w-[15rem] flex-wrap gap-2">
                      <Link
                        href={`/teacher/students/${row.student_id}/performance`}
                      >
                        <Button variant="secondary">Performance</Button>
                      </Link>
                      <Link
                        href={`/teacher/students/${row.student_id}/progress-report`}
                        data-testid="student-progress-link"
                      >
                        <Button variant="secondary">Progress Report</Button>
                      </Link>
                    </div>
                  )
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No weak students detected yet."
          description="Students who need academic support will appear here after graded submissions exist."
        />
      )}
    </>
  );
}
