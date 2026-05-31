"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminWeakStudents } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminWeakStudent } from "@/types/analytics";
import {
  formatPercentage,
  ScoreBadge,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

export default function AdminWeakStudentsPage() {
  const [rows, setRows] = useState<AdminWeakStudent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRows() {
      try {
        setRows(await getAdminWeakStudents());
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

    void loadRows();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading weak students..." />;
  }

  if (error) {
    return <EmptyState title="Weak students unavailable" description={error} />;
  }

  const highRiskCount = rows.filter((row) => row.risk_level === "high").length;
  const missedAssignmentCount = rows.reduce(
    (total, row) => total + row.missed_assignment_count,
    0
  );

  return (
    <>
      <PageHeader
        title="School Weak Students"
        description="Review learners who may need academic intervention across the school."
      />

      {rows.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Weak students" value={rows.length} />
            <StatCard label="High risk" value={highRiskCount} />
            <StatCard label="Missed assignments" value={missedAssignmentCount} />
            <StatCard
              label="Lowest average"
              value={formatPercentage(
                Math.min(...rows.map((row) => row.average_percentage))
              )}
            />
          </section>

          <section className="mt-6">
            <DataTable<AdminWeakStudent>
              data={rows}
              columns={[
                {
                  key: "student_name",
                  header: "Student",
                  render: (row) => (
                    <span className="font-semibold">{row.student_name}</span>
                  )
                },
                {
                  key: "admission_number",
                  header: "Admission number",
                  render: (row) => row.admission_number ?? "Not set"
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
                      <ScoreBadge percentage={row.average_percentage} />
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
                  key: "weak_subjects",
                  header: "Weak subjects",
                  render: (row) =>
                    row.weak_subjects.length ? (
                      <div className="min-w-[12rem] space-y-1">
                        {row.weak_subjects.slice(0, 3).map((subject) => (
                          <p key={subject.subject} className="text-sm text-ink">
                            {subject.subject} -{" "}
                            {formatPercentage(subject.average_percentage)}
                          </p>
                        ))}
                      </div>
                    ) : (
                      "None listed"
                    )
                },
                {
                  key: "weak_topics",
                  header: "Weak topics",
                  render: (row) =>
                    row.weak_topics.length ? (
                      <div className="min-w-[12rem] space-y-1">
                        {row.weak_topics.slice(0, 3).map((topic) => (
                          <p
                            key={`${topic.subject ?? "subject"}-${topic.topic}`}
                            className="text-sm text-ink"
                          >
                            {topic.topic} - {formatPercentage(topic.average_percentage)}
                          </p>
                        ))}
                      </div>
                    ) : (
                      "None listed"
                    )
                },
                {
                  key: "risk_level",
                  header: "Risk",
                  render: (row) => <StatusBadge value={row.risk_level} />
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
                    <Link
                      href={`/admin/students/${row.student_id}/progress-report`}
                      data-testid="student-progress-link"
                    >
                      <Button variant="secondary">Progress Report</Button>
                    </Link>
                  )
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No weak students detected yet"
          description="School-wide weak student alerts will appear after graded submissions exist."
        />
      )}
    </>
  );
}
