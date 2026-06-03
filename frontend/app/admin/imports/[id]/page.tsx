"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getBulkImport, getBulkImportRows } from "@/lib/bulkImports";
import type {
  BulkImportBatch,
  BulkImportDomain,
  BulkImportRow,
  BulkImportRowStatus
} from "@/types/bulkImports";

const rowStatusTone: Record<
  BulkImportRowStatus,
  "neutral" | "success" | "warning" | "danger"
> = {
  pending: "neutral",
  imported: "success",
  warning: "warning",
  failed: "danger",
  duplicate: "warning"
};

function isDomain(value: string | null): value is BulkImportDomain {
  return value === "accounts" || value === "academics";
}

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

function SummaryCard({
  label,
  value
}: {
  label: string;
  value: string | number;
}) {
  return (
    <Card>
      <p className="text-sm font-medium text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </Card>
  );
}

function RowStatusBadge({ status }: { status: BulkImportRowStatus }) {
  return <Badge tone={rowStatusTone[status]}>{status.replaceAll("_", " ")}</Badge>;
}

function rawDataSummary(row: BulkImportRow) {
  const entries = Object.entries(row.raw_data ?? {}).filter(([, value]) => value);
  if (!entries.length) {
    return "No raw data";
  }
  return entries
    .slice(0, 6)
    .map(([key, value]) => `${key}: ${value}`)
    .join(" | ");
}

export default function BulkImportDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const domainParam = searchParams.get("domain");
  const domain: BulkImportDomain = isDomain(domainParam) ? domainParam : "accounts";
  const [batch, setBatch] = useState<BulkImportBatch | null>(null);
  const [rows, setRows] = useState<BulkImportRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadImport = useCallback(async () => {
    setIsLoading(true);
    try {
      const [batchPayload, rowPayload] = await Promise.all([
        getBulkImport(domain, params.id),
        getBulkImportRows(domain, params.id)
      ]);
      setBatch({ ...batchPayload, domain });
      setRows(rowPayload);
      setError("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load import.");
    } finally {
      setIsLoading(false);
    }
  }, [domain, params.id]);

  useEffect(() => {
    void loadImport();
  }, [loadImport]);

  if (isLoading && !batch) {
    return <LoadingState label="Loading import details..." />;
  }

  if (error && !batch) {
    return <EmptyState title="Import unavailable" description={error} />;
  }

  if (!batch) {
    return <EmptyState title="Import not found" description="This import could not be loaded." />;
  }

  return (
    <>
      <PageHeader
        title="Bulk Import Detail"
        description={`${batch.import_type.replaceAll("_", " ")} from ${batch.original_filename || "CSV file"}.`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/imports/new">
              <Button>New Import</Button>
            </Link>
            <Link href="/admin/imports">
              <Button variant="secondary">Back to Imports</Button>
            </Link>
          </div>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <section
        className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-6"
        data-testid="bulk-import-detail-page"
      >
        <SummaryCard label="Total rows" value={batch.total_rows} />
        <SummaryCard label="Imported rows" value={batch.successful_rows} />
        <SummaryCard label="Failed rows" value={batch.failed_rows} />
        <SummaryCard label="Duplicate rows" value={batch.duplicate_rows} />
        <SummaryCard label="Warning rows" value={batch.warning_rows} />
        <SummaryCard label="Status" value={batch.status.replaceAll("_", " ")} />
      </section>

      <Card className="mb-6">
        <div className="flex flex-wrap gap-2">
          <Badge tone="neutral">{batch.domain}</Badge>
          <Badge tone={batch.status === "completed" ? "success" : batch.status === "failed" ? "danger" : "warning"}>
            {batch.status.replaceAll("_", " ")}
          </Badge>
        </div>
        <p className="mt-3 text-sm leading-6 text-muted">
          Created {formatDate(batch.created_at)} by {batch.uploaded_by_name || "Unknown"}.
          {batch.error_message ? ` Latest error: ${batch.error_message}` : ""}
        </p>
      </Card>

      <DataTable<BulkImportRow>
        data={rows}
        emptyTitle="No import rows"
        emptyDescription="No row records were found for this import."
        columns={[
          { key: "row_number", header: "Row", render: (row) => row.row_number },
          {
            key: "status",
            header: "Status",
            render: (row) => (
              <span data-testid="bulk-import-row-status">
                <RowStatusBadge status={row.status} />
              </span>
            )
          },
          {
            key: "created",
            header: "Created record",
            render: (row) =>
              row.user_name ||
              row.user_email ||
              row.student_enrollment_display ||
              row.teacher_assignment_display ||
              "None"
          },
          {
            key: "raw_data",
            header: "Raw data",
            render: (row) => (
              <span className="block min-w-[22rem] text-sm">{rawDataSummary(row)}</span>
            )
          },
          {
            key: "warning_message",
            header: "Warning",
            render: (row) => row.warning_message || "None"
          },
          {
            key: "error_message",
            header: "Error",
            render: (row) => row.error_message || "None"
          }
        ]}
      />
    </>
  );
}
