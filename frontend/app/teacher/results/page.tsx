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
import { getAssignments } from "@/lib/academics";
import { ApiError } from "@/lib/api";
import type { Assignment, AssignmentStatus } from "@/types/academics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

const statusTone: Record<AssignmentStatus, BadgeTone> = {
  draft: "warning",
  published: "success",
  closed: "neutral",
  archived: "danger"
};

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

export default function TeacherResultsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAssignments() {
      try {
        setAssignments(await getAssignments());
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Unable to load results."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAssignments();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading results..." />;
  }

  if (error) {
    return <EmptyState title="Results unavailable" description={error} />;
  }

  const publishedCount = assignments.filter(
    (assignment) => assignment.status === "published"
  ).length;
  const closedCount = assignments.filter(
    (assignment) => assignment.status === "closed"
  ).length;

  return (
    <>
      <PageHeader
        title="Results"
        description="Open assignment-level analytics and review class performance."
      />

      {assignments.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Assignments" value={assignments.length} />
            <StatCard label="Published" value={publishedCount} />
            <StatCard label="Closed" value={closedCount} />
            <StatCard
              label="Questions assigned"
              value={assignments.reduce(
                (total, assignment) => total + assignment.question_count,
                0
              )}
            />
          </section>

          <section className="mt-6">
            <DataTable<Assignment>
              data={assignments}
              columns={[
                {
                  key: "title",
                  header: "Title",
                  render: (row) => (
                    <span className="block min-w-[14rem] font-semibold">
                      {row.title}
                    </span>
                  )
                },
                {
                  key: "class_arm_name",
                  header: "Class arm",
                  render: (row) => row.class_arm_name ?? "Not set"
                },
                {
                  key: "subject_name",
                  header: "Subject",
                  render: (row) => row.subject_name ?? "Not set"
                },
                {
                  key: "topic_title",
                  header: "Topic",
                  render: (row) => row.topic_title ?? "Not set"
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => (
                    <Badge tone={statusTone[row.status]}>{row.status}</Badge>
                  )
                },
                {
                  key: "due_at",
                  header: "Due date",
                  render: (row) => formatDate(row.due_at)
                },
                {
                  key: "action",
                  header: "Action",
                  render: (row) => (
                    <Link href={`/teacher/assignments/${row.id}/results`}>
                      <Button variant="secondary">View Results</Button>
                    </Link>
                  )
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No assignments yet"
          description="Assignment results will appear here after you create assignments."
        />
      )}
    </>
  );
}
