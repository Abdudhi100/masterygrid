"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminAssignmentCompliance } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminAssignmentCompliance } from "@/types/analytics";
import {
  formatDate,
  formatPercentage,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

export default function AdminAssignmentCompliancePage() {
  const [rows, setRows] = useState<AdminAssignmentCompliance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRows() {
      try {
        setRows(await getAdminAssignmentCompliance());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load assignment compliance."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadRows();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading assignment compliance..." />;
  }

  if (error) {
    return (
      <EmptyState title="Assignment compliance unavailable" description={error} />
    );
  }

  const poorCount = rows.filter(
    (row) => row.compliance_status === "poor"
  ).length;
  const expectedStudents = rows.reduce(
    (total, row) => total + row.expected_students,
    0
  );
  const submittedCount = rows.reduce(
    (total, row) => total + row.submitted_count,
    0
  );

  return (
    <>
      <PageHeader
        title="Assignment Compliance"
        description="Track assignment completion, not-started counts, and submission rates."
      />

      {rows.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Assignments" value={rows.length} />
            <StatCard label="Expected students" value={expectedStudents} />
            <StatCard label="Submitted" value={submittedCount} />
            <StatCard label="Poor compliance" value={poorCount} />
          </section>

          <section className="mt-6">
            <DataTable<AdminAssignmentCompliance>
              data={rows}
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
                  key: "teacher_name",
                  header: "Teacher"
                },
                {
                  key: "class_arm",
                  header: "Class arm"
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
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge value={row.status} />
                },
                {
                  key: "due_at",
                  header: "Due date",
                  render: (row) => formatDate(row.due_at)
                },
                {
                  key: "expected_students",
                  header: "Expected"
                },
                {
                  key: "started_count",
                  header: "Started"
                },
                {
                  key: "submitted_count",
                  header: "Submitted"
                },
                {
                  key: "graded_count",
                  header: "Graded"
                },
                {
                  key: "not_started_count",
                  header: "Not started"
                },
                {
                  key: "submission_rate",
                  header: "Submission rate",
                  render: (row) => formatPercentage(row.submission_rate)
                },
                {
                  key: "compliance_status",
                  header: "Compliance",
                  render: (row) => <StatusBadge value={row.compliance_status} />
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No assignment compliance yet"
          description="Compliance analytics will appear after assignments are created."
        />
      )}
    </>
  );
}
