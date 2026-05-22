"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminClassPerformance } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminClassPerformance } from "@/types/analytics";
import {
  formatPercentage,
  ScoreBadge,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

export default function AdminClassPerformancePage() {
  const [rows, setRows] = useState<AdminClassPerformance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRows() {
      try {
        setRows(await getAdminClassPerformance());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load class performance."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadRows();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading class performance..." />;
  }

  if (error) {
    return <EmptyState title="Class performance unavailable" description={error} />;
  }

  const highRiskCount = rows.filter((row) => row.risk_level === "high").length;
  const totalStudents = rows.reduce((total, row) => total + row.total_students, 0);
  const totalSubmissions = rows.reduce(
    (total, row) => total + row.total_submissions,
    0
  );

  return (
    <>
      <PageHeader
        title="Class Performance"
        description="Compare class-level performance, submission coverage, and intervention risk."
      />

      {rows.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Class arms" value={rows.length} />
            <StatCard label="Students" value={totalStudents} />
            <StatCard label="Submissions" value={totalSubmissions} />
            <StatCard label="High-risk classes" value={highRiskCount} />
          </section>

          <section className="mt-6">
            <DataTable<AdminClassPerformance>
              data={rows}
              columns={[
                {
                  key: "class_level",
                  header: "Class level"
                },
                {
                  key: "class_arm_name",
                  header: "Class arm",
                  render: (row) => (
                    <span className="font-semibold">{row.class_arm_name}</span>
                  )
                },
                {
                  key: "total_students",
                  header: "Students"
                },
                {
                  key: "total_assignments",
                  header: "Assignments"
                },
                {
                  key: "total_submissions",
                  header: "Submissions"
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
                  key: "submission_rate",
                  header: "Submission rate",
                  render: (row) => formatPercentage(row.submission_rate)
                },
                {
                  key: "weak_student_count",
                  header: "Weak students"
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
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No class performance yet"
          description="Class analytics will appear after assignments and submissions exist."
        />
      )}
    </>
  );
}
