"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  QuestionImportRowStatusBadge,
  QuestionImportStatusBadge
} from "@/components/question-bank/QuestionImportBadges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import {
  getQuestionImport,
  getQuestionImportRows
} from "@/lib/questionBank";
import type {
  QuestionImportBatch,
  QuestionImportRow
} from "@/types/questionBank";

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

function shortHash(value: string) {
  return value ? `${value.slice(0, 10)}...` : "Not set";
}

const diagramFields = [
  "has_diagram",
  "diagram_file_name",
  "diagram_url",
  "diagram_description",
  "needs_manual_review"
];

function rawValue(row: QuestionImportRow, key: string) {
  const value = row.raw_data[key];
  if (value === null || value === undefined || value === "") {
    return "";
  }
  return String(value);
}

function diagramData(row: QuestionImportRow) {
  return diagramFields
    .map((field) => ({ field, value: rawValue(row, field) }))
    .filter((item) => item.value);
}

export default function QuestionImportDetailPage({
  params
}: {
  params: { id: string };
}) {
  const [batch, setBatch] = useState<QuestionImportBatch | null>(null);
  const [rows, setRows] = useState<QuestionImportRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadImport = useCallback(async () => {
    setIsLoading(true);
    try {
      const [batchData, rowData] = await Promise.all([
        getQuestionImport(params.id),
        getQuestionImportRows(params.id)
      ]);
      setBatch(batchData);
      setRows(rowData);
      setError("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load import.");
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadImport();
  }, [loadImport]);

  if (isLoading) {
    return <LoadingState label="Loading import details..." />;
  }

  if (error && !batch) {
    return <EmptyState title="Import unavailable" description={error} />;
  }

  if (!batch) {
    return (
      <EmptyState
        title="Import not found"
        description="This import batch could not be found or you do not have access."
      />
    );
  }

  return (
    <>
      <PageHeader
        title={batch.title}
        description="Inspect row-level import results and review draft questions before approval."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/question-bank/imports">
              <Button variant="secondary">Back to Imports</Button>
            </Link>
            <Link href="/admin/question-bank?status=draft">
              <Button variant="secondary">View Imported Draft Questions</Button>
            </Link>
            <Link href="/admin/question-bank">
              <Button>Go to Question Bank</Button>
            </Link>
          </div>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card className="mb-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap gap-2">
              <QuestionImportStatusBadge status={batch.status} />
              <span className="rounded-full bg-surface px-2.5 py-1 text-xs font-semibold text-muted">
                {batch.file_type.toUpperCase()}
              </span>
            </div>
            <dl className="mt-4 grid gap-4 text-sm text-muted sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="font-semibold text-ink">Original file</dt>
                <dd className="mt-1">{batch.original_filename || "Not set"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Uploaded by</dt>
                <dd className="mt-1">{batch.uploaded_by_name ?? "Unknown"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Source</dt>
                <dd className="mt-1">{batch.source_name ?? "From CSV rows"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Created</dt>
                <dd className="mt-1">{formatDate(batch.created_at)}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Processed</dt>
                <dd className="mt-1">{formatDate(batch.processed_at)}</dd>
              </div>
            </dl>
          </div>
        </div>
      </Card>

      <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Total rows", batch.total_rows],
          ["Successful rows", batch.successful_rows],
          ["Failed rows", batch.failed_rows],
          ["Duplicate rows", batch.duplicate_rows]
        ].map(([label, value]) => (
          <Card key={label}>
            <p className="text-sm font-medium text-muted">{label}</p>
            <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
          </Card>
        ))}
      </section>

      {batch.error_summary ? (
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <h2 className="text-base font-semibold text-ink">Error Summary</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-warning">
            {batch.error_summary}
          </p>
        </Card>
      ) : null}

      <DataTable<QuestionImportRow>
        data={rows}
        emptyTitle="No rows found"
        emptyDescription="This import batch does not have row-level results."
        columns={[
          {
            key: "row_number",
            header: "Row",
            render: (row) => row.row_number
          },
          {
            key: "status",
            header: "Status",
            render: (row) => <QuestionImportRowStatusBadge status={row.status} />
          },
          {
            key: "error_message",
            header: "Error",
            render: (row) => (
              <span className="block min-w-[16rem] max-w-xl leading-6">
                {row.error_message || "No error"}
              </span>
            )
          },
          {
            key: "question",
            header: "Question",
            render: (row) =>
              row.question ? (
                <Link
                  href={`/admin/question-bank/${row.question}`}
                  className="font-semibold text-brand-700 hover:underline"
                >
                  {row.question_text ?? `Question ${row.question}`}
                </Link>
              ) : (
                "Not imported"
              )
          },
          {
            key: "content_hash",
            header: "Content hash",
            render: (row) => shortHash(row.content_hash)
          },
          {
            key: "diagram_data",
            header: "Diagram data",
            render: (row) => {
              const values = diagramData(row);
              if (!values.length) {
                return "No diagram data";
              }

              return (
                <div className="min-w-[16rem] space-y-1 text-xs leading-5">
                  {values.map((item) => (
                    <p key={item.field}>
                      <span className="font-semibold text-ink">
                        {item.field}:
                      </span>{" "}
                      <span className="text-muted">{item.value}</span>
                    </p>
                  ))}
                </div>
              );
            }
          }
        ]}
      />
    </>
  );
}
