"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import {
  createBulkImport,
  domainForImportType,
  preflightBulkImport
} from "@/lib/bulkImports";
import type {
  BulkImportIssue,
  BulkImportPreflightResponse,
  BulkImportPreflightRowStatus,
  BulkImportType
} from "@/types/bulkImports";

const importTypeOptions: { value: BulkImportType; label: string }[] = [
  { value: "students", label: "Students" },
  { value: "teachers", label: "Teachers" },
  { value: "student_enrollments", label: "Student Enrollments" },
  { value: "teacher_assignments", label: "Teacher Assignments" }
];

const templateColumns: Record<BulkImportType, string[]> = {
  students: [
    "full_name",
    "email",
    "admission_number",
    "class_arm",
    "guardian_name",
    "guardian_phone",
    "phone_number",
    "password"
  ],
  teachers: ["full_name", "email", "staff_id", "phone_number", "password"],
  student_enrollments: [
    "student_email",
    "admission_number",
    "academic_session",
    "term",
    "class_arm"
  ],
  teacher_assignments: [
    "teacher_email",
    "staff_id",
    "class_arm",
    "subject",
    "academic_session",
    "term"
  ]
};

const statusTone: Record<
  BulkImportPreflightRowStatus,
  "neutral" | "success" | "warning" | "danger"
> = {
  valid: "success",
  valid_with_warnings: "warning",
  invalid: "danger",
  duplicate: "warning"
};

function isSupportedFile(file: File) {
  return file.name.toLowerCase().endsWith(".csv");
}

function issueText(issues: BulkImportIssue[]) {
  return issues.map((issue) => `${issue.field}: ${issue.message}`);
}

function downloadTemplate(importType: BulkImportType) {
  const columns = templateColumns[importType];
  const csv = `${columns.join(",")}\n`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${importType}-bulk-import-template.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function SummaryCard({
  label,
  value,
  tone = "neutral"
}: {
  label: string;
  value: string | number;
  tone?: "neutral" | "success" | "warning" | "danger" | "brand";
}) {
  const toneClasses = {
    neutral: "border-line bg-white",
    success: "border-emerald-100 bg-emerald-50",
    warning: "border-amber-100 bg-amber-50",
    danger: "border-red-100 bg-red-50",
    brand: "border-brand-100 bg-brand-50"
  };
  return (
    <Card className={toneClasses[tone]}>
      <p className="text-sm font-medium text-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
    </Card>
  );
}

function IssueList({
  issues,
  tone
}: {
  issues: BulkImportIssue[];
  tone: "danger" | "warning";
}) {
  if (!issues.length) {
    return <span className="text-muted">None</span>;
  }
  return (
    <ul
      className={`min-w-[14rem] space-y-1 leading-5 ${
        tone === "danger" ? "text-danger" : "text-warning"
      }`}
    >
      {issueText(issues).map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function arraySummary(values?: string[]) {
  if (!values?.length) {
    return "None";
  }
  const visible = values.slice(0, 4).join(", ");
  const remaining = values.length - 4;
  return remaining > 0 ? `${visible} +${remaining} more` : visible;
}

function PreflightReport({ report }: { report: BulkImportPreflightResponse }) {
  const rows = report.rows.slice(0, 100);
  const summary = report.summary;

  return (
    <div className="mt-6 space-y-6">
      <section
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6"
        data-testid="bulk-import-preflight-summary"
      >
        <SummaryCard label="Total Rows" value={report.total_rows} />
        <SummaryCard label="Valid Rows" value={report.valid_rows} tone="success" />
        <SummaryCard
          label="Invalid Rows"
          value={report.invalid_rows}
          tone={report.invalid_rows ? "danger" : "neutral"}
        />
        <SummaryCard
          label="Warning Rows"
          value={report.warning_rows}
          tone={report.warning_rows ? "warning" : "neutral"}
        />
        <SummaryCard
          label="Duplicate Rows"
          value={report.duplicate_rows}
          tone={report.duplicate_rows ? "warning" : "neutral"}
        />
        <SummaryCard
          label="Can Import"
          value={report.can_import ? "Yes" : "No"}
          tone={report.can_import ? "success" : "danger"}
        />
      </section>

      <Card>
        <div className="flex flex-wrap gap-2">
          <Badge tone={report.can_import ? "success" : "danger"}>
            {report.can_import ? "ready to import" : "fix invalid rows"}
          </Badge>
          <Badge tone="neutral">{report.import_type.replaceAll("_", " ")}</Badge>
        </div>
        <div className="mt-4 space-y-2 text-sm leading-6 text-muted">
          {!report.can_import ? (
            <p className="text-danger">
              Fix the invalid rows in your CSV and validate again before importing.
            </p>
          ) : null}
          {report.warning_rows ? (
            <p className="text-warning">
              Warnings and duplicates do not block import, but affected rows may be
              skipped or need review.
            </p>
          ) : null}
          <p>Imported users and academic records are scoped to your school.</p>
          <p>
            If a password is blank, the backend creates a secure password. It is
            not displayed in normal API responses; use your onboarding/password
            reset process when needed.
          </p>
        </div>
      </Card>

      <Card>
        <h2 className="text-base font-semibold text-ink">Issue Summary</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[
            ["Missing required fields", summary.missing_required_fields ?? 0],
            ["Invalid emails", summary.invalid_emails ?? 0],
            ["Duplicate emails", summary.duplicate_emails ?? 0],
            ["Existing emails", summary.existing_emails ?? 0],
            ["Duplicate IDs", summary.duplicate_identifiers ?? 0],
            ["Existing IDs", summary.existing_identifiers ?? 0],
            ["Missing students", summary.missing_students ?? 0],
            ["Missing teachers", summary.missing_teachers ?? 0],
            ["Existing records", summary.existing_records ?? 0],
            ["Missing class arms", arraySummary(summary.missing_class_arms)],
            ["Missing subjects", arraySummary(summary.missing_subjects)],
            ["Missing sessions", arraySummary(summary.missing_academic_sessions)],
            ["Missing terms", arraySummary(summary.missing_terms)]
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-line bg-white px-3 py-2">
              <p className="text-xs font-semibold uppercase text-muted">{label}</p>
              <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-ink">Row-Level Report</h2>
          {report.rows.length > rows.length ? (
            <p className="text-sm text-warning">
              Showing first 100 of {report.rows.length} rows.
            </p>
          ) : null}
        </div>
        <div className="mt-4 overflow-hidden rounded-lg border border-line bg-white">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-line text-sm">
              <thead className="bg-surface">
                <tr>
                  {[
                    "Row",
                    "Status",
                    "Name/Person",
                    "Email/ID",
                    "Class Arm",
                    "Subject",
                    "Session",
                    "Term",
                    "Errors",
                    "Warnings"
                  ].map((heading) => (
                    <th key={heading} className="px-4 py-3 text-left font-semibold text-muted">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {rows.map((row) => (
                  <tr key={row.row_number} className="align-top hover:bg-surface">
                    <td className="px-4 py-3 text-ink">{row.row_number}</td>
                    <td className="px-4 py-3">
                      <Badge tone={statusTone[row.status]}>
                        {row.status.replaceAll("_", " ")}
                      </Badge>
                      {row.duplicate_type ? (
                        <p className="mt-1 text-xs text-muted">
                          {row.duplicate_type.replace("_", " ")}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-ink">
                      {row.full_name || row.student || row.teacher || "Not set"}
                    </td>
                    <td className="px-4 py-3 text-ink">
                      {row.email || row.identifier || "Not set"}
                    </td>
                    <td className="px-4 py-3 text-ink">{row.class_arm || "Not set"}</td>
                    <td className="px-4 py-3 text-ink">{row.subject || "Not set"}</td>
                    <td className="px-4 py-3 text-ink">
                      {row.academic_session || "Not set"}
                    </td>
                    <td className="px-4 py-3 text-ink">{row.term || "Not set"}</td>
                    <td className="px-4 py-3">
                      <IssueList issues={row.errors} tone="danger" />
                    </td>
                    <td className="px-4 py-3">
                      <IssueList issues={row.warnings} tone="warning" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default function NewBulkImportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialType = (searchParams.get("type") as BulkImportType | null) ?? "students";
  const [importType, setImportType] = useState<BulkImportType>(
    importTypeOptions.some((option) => option.value === initialType) ? initialType : "students"
  );
  const [file, setFile] = useState<File | null>(null);
  const [preflight, setPreflight] = useState<BulkImportPreflightResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState("");

  const domain = domainForImportType(importType);
  const selectedFileLabel = useMemo(() => {
    if (!file) {
      return "No file selected";
    }
    return `${file.name} (${Math.max(1, Math.round(file.size / 1024))} KB)`;
  }, [file]);

  function buildFormData() {
    const formData = new FormData();
    formData.set("import_type", importType);
    if (file) {
      formData.set("file", file);
    }
    return formData;
  }

  function handleFileChange(selectedFile: File | null) {
    setFile(selectedFile);
    setPreflight(null);
    if (selectedFile && !isSupportedFile(selectedFile)) {
      setError("Only .csv files are supported for bulk user and enrollment imports.");
    } else {
      setError("");
    }
  }

  async function handleValidate() {
    setError("");
    if (!file) {
      setError("Choose a CSV file to validate.");
      return;
    }
    if (!isSupportedFile(file)) {
      setError("Only .csv files are supported for bulk user and enrollment imports.");
      return;
    }

    setIsValidating(true);
    try {
      setPreflight(await preflightBulkImport(domain, buildFormData()));
    } catch (err) {
      setPreflight(null);
      setError(err instanceof ApiError ? err.message : "Unable to validate import file.");
    } finally {
      setIsValidating(false);
    }
  }

  async function handleImport() {
    setError("");
    if (!preflight) {
      setError("Validate the file before importing.");
      return;
    }
    if (!preflight.can_import) {
      setError("Fix invalid rows and validate again before importing.");
      return;
    }
    if (!file) {
      setError("Choose a CSV file to import.");
      return;
    }

    setIsImporting(true);
    try {
      const batch = await createBulkImport(domain, buildFormData());
      router.push(`/admin/imports/${batch.id}?domain=${domain}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to import file.");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="New Bulk Import"
        description="Validate CSV files before creating students, teachers, enrollments, or teacher assignments."
        actions={
          <Link href="/admin/imports">
            <Button variant="secondary">Back to Imports</Button>
          </Link>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <Card>
          <div className="space-y-4">
            <Select
              label="Import type"
              data-testid="bulk-import-type-select"
              value={importType}
              options={importTypeOptions}
              onChange={(event) => {
                setImportType(event.target.value as BulkImportType);
                setPreflight(null);
              }}
            />
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-ink">CSV file</span>
              <input
                type="file"
                data-testid="bulk-import-file-input"
                accept=".csv,text/csv"
                className="block w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink file:mr-4 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-brand-700"
                onChange={(event) =>
                  handleFileChange(event.target.files?.[0] ?? null)
                }
              />
              <span className="mt-2 block text-xs text-muted">{selectedFileLabel}</span>
            </label>
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                variant="secondary"
                data-testid="bulk-import-validate-button"
                isLoading={isValidating}
                disabled={!file || isImporting}
                onClick={handleValidate}
              >
                Validate File
              </Button>
              <Button
                type="button"
                data-testid="bulk-import-now-button"
                isLoading={isImporting}
                disabled={!preflight?.can_import || isValidating}
                onClick={handleImport}
              >
                Import Now
              </Button>
              <Button
                type="button"
                variant="secondary"
                data-testid="bulk-import-template-button"
                onClick={() => downloadTemplate(importType)}
              >
                Download Template
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">CSV Format</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Choose the import type first; each type has different required columns.
            Preflight checks for missing users, academic records, duplicates, and
            school-scope mismatches before import.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {templateColumns[importType].map((column) => (
              <span
                key={column}
                className="rounded-md bg-surface px-2 py-1 text-xs font-semibold text-muted"
              >
                {column}
              </span>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-muted">
            Students and teachers with duplicate emails or school identifiers are
            skipped. Preflight creates no records.
          </p>
        </Card>
      </div>

      {preflight ? <PreflightReport report={preflight} /> : null}
    </>
  );
}
