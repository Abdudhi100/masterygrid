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
import { ApiError } from "@/lib/api";
import { getAllBulkImports } from "@/lib/bulkImports";
import type { BulkImportBatch, BulkImportBatchStatus, BulkImportType } from "@/types/bulkImports";

const importTypeLabels: Record<BulkImportType, string> = {
  students: "Students",
  teachers: "Teachers",
  student_enrollments: "Student Enrollments",
  teacher_assignments: "Teacher Assignments"
};

const statusTone: Record<BulkImportBatchStatus, "neutral" | "success" | "warning" | "danger" | "brand"> = {
  pending: "neutral",
  processing: "brand",
  completed: "success",
  completed_with_errors: "warning",
  failed: "danger"
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

function StatusBadge({ status }: { status: BulkImportBatchStatus }) {
  return <Badge tone={statusTone[status]}>{status.replaceAll("_", " ")}</Badge>;
}

export default function AdminBulkImportsPage() {
  const [imports, setImports] = useState<BulkImportBatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadImports = useCallback(async () => {
    setIsLoading(true);
    try {
      setImports(await getAllBulkImports());
      setError("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load bulk imports.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadImports();
  }, [loadImports]);

  if (isLoading && !imports.length) {
    return <LoadingState label="Loading bulk imports..." />;
  }

  if (error && !imports.length) {
    return <EmptyState title="Bulk imports unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Bulk Imports"
        description="Validate and import students, teachers, enrollments, and teacher class-subject assignments from CSV files."
        actions={
          <Link href="/admin/imports/new">
            <Button>New Bulk Import</Button>
          </Link>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card className="mb-4">
        <p className="text-sm leading-6 text-muted">
          Bulk import is school-scoped and validates files before records are created.
          Duplicate rows are skipped during import rather than crashing the full batch.
        </p>
      </Card>

      {isLoading ? (
        <LoadingState label="Refreshing bulk imports..." />
      ) : (
        <DataTable<BulkImportBatch>
          data={imports}
          emptyTitle="No bulk imports yet"
          emptyDescription="Upload a CSV file to start onboarding users and academic assignments."
          columns={[
            {
              key: "import_type",
              header: "Type",
              render: (row) => importTypeLabels[row.import_type]
            },
            {
              key: "original_filename",
              header: "File",
              render: (row) => row.original_filename || "Not set"
            },
            {
              key: "domain",
              header: "Domain",
              render: (row) => <Badge tone="neutral">{row.domain}</Badge>
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <StatusBadge status={row.status} />
            },
            { key: "total_rows", header: "Total", render: (row) => row.total_rows },
            {
              key: "successful_rows",
              header: "Imported",
              render: (row) => row.successful_rows
            },
            { key: "failed_rows", header: "Failed", render: (row) => row.failed_rows },
            {
              key: "duplicate_rows",
              header: "Duplicates",
              render: (row) => row.duplicate_rows
            },
            {
              key: "warning_rows",
              header: "Warnings",
              render: (row) => row.warning_rows
            },
            {
              key: "created_at",
              header: "Created",
              render: (row) => formatDate(row.created_at)
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <Link href={`/admin/imports/${row.id}?domain=${row.domain}`}>
                  <Button variant="secondary">View Details</Button>
                </Link>
              )
            }
          ]}
        />
      )}
    </>
  );
}
