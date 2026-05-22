"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminTeacherActivity } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminTeacherActivity } from "@/types/analytics";
import {
  formatDate,
  formatPercentage,
  ScoreBadge,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

export default function AdminTeacherActivityPage() {
  const [rows, setRows] = useState<AdminTeacherActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRows() {
      try {
        setRows(await getAdminTeacherActivity());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load teacher activity."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadRows();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading teacher activity..." />;
  }

  if (error) {
    return <EmptyState title="Teacher activity unavailable" description={error} />;
  }

  const activeCount = rows.filter((row) => row.activity_status === "active").length;
  const inactiveCount = rows.filter(
    (row) => row.activity_status === "inactive"
  ).length;

  return (
    <>
      <PageHeader
        title="Teacher Activity"
        description="Monitor assignment creation, publishing behavior, and class outcomes by teacher."
      />

      {rows.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Teachers" value={rows.length} />
            <StatCard label="Active" value={activeCount} />
            <StatCard label="Inactive" value={inactiveCount} />
            <StatCard
              label="Assignments created"
              value={rows.reduce(
                (total, row) => total + row.assignments_created,
                0
              )}
            />
          </section>

          <section className="mt-6">
            <DataTable<AdminTeacherActivity>
              data={rows}
              columns={[
                {
                  key: "teacher_name",
                  header: "Teacher",
                  render: (row) => (
                    <span className="font-semibold">{row.teacher_name}</span>
                  )
                },
                {
                  key: "staff_id",
                  header: "Staff ID",
                  render: (row) => row.staff_id ?? "Not set"
                },
                {
                  key: "assigned_classes_count",
                  header: "Classes"
                },
                {
                  key: "assigned_subjects_count",
                  header: "Subjects"
                },
                {
                  key: "assignments_created",
                  header: "Created"
                },
                {
                  key: "published_assignments",
                  header: "Published"
                },
                {
                  key: "total_student_submissions",
                  header: "Submissions"
                },
                {
                  key: "average_class_performance",
                  header: "Class average",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.average_class_performance)}</span>
                      <ScoreBadge percentage={row.average_class_performance} />
                    </div>
                  )
                },
                {
                  key: "last_assignment_date",
                  header: "Last assignment",
                  render: (row) => formatDate(row.last_assignment_date)
                },
                {
                  key: "activity_status",
                  header: "Activity",
                  render: (row) => <StatusBadge value={row.activity_status} />
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
          title="No teacher activity yet"
          description="Teacher activity analytics will appear once teachers create assignments."
        />
      )}
    </>
  );
}
