"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  QuestionImportFileTypeBadge,
  QuestionImportStatusBadge
} from "@/components/question-bank/QuestionImportBadges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getQuestionImports } from "@/lib/questionBank";
import type { QuestionImportBatch } from "@/types/questionBank";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not processed";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not processed";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

export default function AdminQuestionImportsPage() {
  const [imports, setImports] = useState<QuestionImportBatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadImports = useCallback(async () => {
    setIsLoading(true);
    try {
      setImports(await getQuestionImports());
      setError("");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load question imports."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadImports();
  }, [loadImports]);

  if (isLoading && !imports.length) {
    return <LoadingState label="Loading question imports..." />;
  }

  if (error && !imports.length) {
    return <EmptyState title="Question imports unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Question Imports"
        description="Upload trusted JAMB and past-exam CSV or ZIP files, then review imported draft questions before approval."
        actions={
          <Link href="/admin/question-bank/imports/new">
            <Button>New Import</Button>
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
          Imports create draft questions only. ZIP imports can attach diagram
          images from the diagrams/ folder when diagram_file_name matches.
          School admins must approve imported questions before teachers can use
          them in assignments.
        </p>
      </Card>

      {isLoading ? (
        <LoadingState label="Refreshing question imports..." />
      ) : (
        <DataTable<QuestionImportBatch>
          data={imports}
          emptyTitle="No imports yet"
          emptyDescription="Upload a CSV or ZIP file to start building the trusted question bank."
          columns={[
            {
              key: "title",
              header: "Title",
              render: (row) => <span className="font-semibold">{row.title}</span>
            },
            {
              key: "original_filename",
              header: "Original file",
              render: (row) => row.original_filename || "Not set"
            },
            {
              key: "file_type",
              header: "File type",
              render: (row) => <QuestionImportFileTypeBadge fileType={row.file_type} />
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <QuestionImportStatusBadge status={row.status} />
            },
            {
              key: "total_rows",
              header: "Total",
              render: (row) => row.total_rows
            },
            {
              key: "successful_rows",
              header: "Successful",
              render: (row) => row.successful_rows
            },
            {
              key: "failed_rows",
              header: "Failed",
              render: (row) => row.failed_rows
            },
            {
              key: "duplicate_rows",
              header: "Duplicates",
              render: (row) => row.duplicate_rows
            },
            {
              key: "warning_rows",
              header: "Warnings",
              render: (row) => row.warning_rows ?? 0
            },
            {
              key: "uploaded_by_name",
              header: "Uploaded by",
              render: (row) => row.uploaded_by_name ?? "Unknown"
            },
            {
              key: "created_at",
              header: "Created",
              render: (row) => formatDate(row.created_at)
            },
            {
              key: "processed_at",
              header: "Processed",
              render: (row) => formatDate(row.processed_at)
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <Link href={`/admin/question-bank/imports/${row.id}`}>
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
