"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { CsvTemplateDownloadButton } from "@/components/question-bank/CsvTemplateDownloadButton";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import {
  createQuestionImport,
  getQuestionSources,
  preflightQuestionImport
} from "@/lib/questionBank";
import type {
  QuestionImportPreflightIssue,
  QuestionImportPreflightResponse,
  QuestionImportPreflightRowStatus,
  QuestionSource
} from "@/types/questionBank";

type Tone = "neutral" | "success" | "warning" | "danger" | "brand";

const requiredColumns = [
  "subject",
  "class_level",
  "topic",
  "source_name",
  "source_type",
  "exam_body",
  "year",
  "difficulty",
  "question_text",
  "option_a",
  "option_b",
  "option_c",
  "option_d",
  "correct_option",
  "explanation"
];

const optionalDiagramColumns = [
  "has_diagram",
  "diagram_file_name",
  "diagram_url",
  "diagram_description",
  "needs_manual_review"
];

const statusTone: Record<QuestionImportPreflightRowStatus, Tone> = {
  valid: "success",
  valid_with_warnings: "warning",
  invalid: "danger",
  duplicate: "warning"
};

const statusLabel: Record<QuestionImportPreflightRowStatus, string> = {
  valid: "valid",
  valid_with_warnings: "valid with warnings",
  invalid: "invalid",
  duplicate: "duplicate"
};

function isSupportedImportFile(file: File) {
  const name = file.name.toLowerCase();
  return name.endsWith(".csv") || name.endsWith(".zip");
}

function formatArraySummary(values: string[]) {
  if (!values.length) {
    return "None";
  }

  const visible = values.slice(0, 4).join(", ");
  const remaining = values.length - 4;
  return remaining > 0 ? `${visible} +${remaining} more` : visible;
}

function issueText(issues: QuestionImportPreflightIssue[]) {
  return issues.map((issue) => `${issue.field}: ${issue.message}`);
}

function SummaryCard({
  label,
  value,
  tone = "neutral"
}: {
  label: string;
  value: string | number;
  tone?: Tone;
}) {
  const toneClasses: Record<Tone, string> = {
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

function RowStatusBadge({
  status
}: {
  status: QuestionImportPreflightRowStatus;
}) {
  return <Badge tone={statusTone[status]}>{statusLabel[status]}</Badge>;
}

function IssueList({
  issues,
  tone
}: {
  issues: QuestionImportPreflightIssue[];
  tone: "danger" | "warning";
}) {
  if (!issues.length) {
    return <span className="text-muted">None</span>;
  }

  const textClass = tone === "danger" ? "text-danger" : "text-warning";
  return (
    <ul className={`min-w-[16rem] space-y-1 leading-5 ${textClass}`}>
      {issueText(issues).map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function PreflightReport({
  report
}: {
  report: QuestionImportPreflightResponse;
}) {
  const rows = report.rows.slice(0, 100);
  const hasHiddenRows = report.rows.length > rows.length;
  const summary = report.summary;

  const issueItems = [
    {
      label: "Missing correct option",
      value: summary.missing_correct_option,
      tone: "danger" as Tone
    },
    {
      label: "Missing options",
      value: summary.missing_options,
      tone: "danger" as Tone
    },
    {
      label: "Missing subjects",
      value: formatArraySummary(summary.missing_subjects),
      active: summary.missing_subjects.length > 0,
      tone: "danger" as Tone
    },
    {
      label: "Missing class levels",
      value: formatArraySummary(summary.missing_class_levels),
      active: summary.missing_class_levels.length > 0,
      tone: "danger" as Tone
    },
    {
      label: "Missing topics",
      value: formatArraySummary(summary.missing_topics),
      active: summary.missing_topics.length > 0,
      tone: "danger" as Tone
    },
    {
      label: "Missing diagrams",
      value: summary.missing_diagrams,
      tone: "warning" as Tone
    },
    {
      label: "Duplicate questions",
      value: summary.duplicate_questions,
      tone: "warning" as Tone
    },
    {
      label: "Existing database duplicates",
      value: summary.existing_database_duplicates,
      tone: "warning" as Tone
    },
    {
      label: "Invalid difficulty",
      value: summary.invalid_difficulty,
      tone: "danger" as Tone
    },
    {
      label: "Invalid correct option",
      value: summary.invalid_correct_option,
      tone: "danger" as Tone
    },
    {
      label: "Invalid source type",
      value: summary.invalid_source_type,
      tone: "danger" as Tone
    },
    {
      label: "Duplicate option texts",
      value: summary.duplicate_option_texts,
      tone: "danger" as Tone
    }
  ];

  return (
    <div className="mt-6 space-y-6">
      <section
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6"
        data-testid="import-preflight-summary"
      >
        <SummaryCard label="Total Rows" value={report.total_rows} />
        <SummaryCard
          label="Valid Rows"
          value={report.valid_rows}
          tone="success"
        />
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
          <Badge tone={report.file_type === "zip" ? "brand" : "neutral"}>
            {report.file_type.toUpperCase()}
          </Badge>
        </div>
        <div className="mt-4 space-y-2 text-sm leading-6 text-muted">
          {!report.can_import ? (
            <p className="text-danger">
              Fix the invalid rows in your CSV/ZIP and validate again before
              importing.
            </p>
          ) : null}
          {report.can_import && report.warning_rows ? (
            <p className="text-warning">
              Warnings will not block import, but affected questions may need
              manual review.
            </p>
          ) : null}
          {report.duplicate_rows ? (
            <p>
              Duplicate rows may be skipped during import depending on current
              import rules.
            </p>
          ) : null}
          <p>Imported questions remain draft until reviewed and approved.</p>
        </div>
      </Card>

      <Card>
        <h2 className="text-base font-semibold text-ink">Issue Summary</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {issueItems.map((item) => {
            const numericValue =
              typeof item.value === "number" ? item.value : undefined;
            const isActive =
              item.active ?? (numericValue !== undefined && numericValue > 0);
            return (
              <div
                key={item.label}
                className={`rounded-md border px-3 py-2 ${
                  isActive && item.tone === "danger"
                    ? "border-red-100 bg-red-50"
                    : isActive && item.tone === "warning"
                      ? "border-amber-100 bg-amber-50"
                      : "border-line bg-white"
                }`}
              >
                <p className="text-xs font-semibold uppercase text-muted">
                  {item.label}
                </p>
                <p className="mt-1 text-sm font-semibold text-ink">
                  {item.value}
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-ink">Row-Level Report</h2>
          {hasHiddenRows ? (
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
                    "Question Preview",
                    "Subject",
                    "Class Level",
                    "Topic",
                    "Diagram File",
                    "Errors",
                    "Warnings"
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-4 py-3 text-left font-semibold text-muted"
                    >
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
                      <div className="space-y-2">
                        <RowStatusBadge status={row.status} />
                        {row.duplicate_type ? (
                          <p className="text-xs text-muted">
                            {row.duplicate_type.replace("_", " ")}
                          </p>
                        ) : null}
                      </div>
                    </td>
                    <td className="min-w-[18rem] px-4 py-3 text-ink">
                      {row.question_preview || "No preview"}
                    </td>
                    <td className="px-4 py-3 text-ink">{row.subject || "Not set"}</td>
                    <td className="px-4 py-3 text-ink">
                      {row.class_level || "Not set"}
                    </td>
                    <td className="px-4 py-3 text-ink">{row.topic || "Not set"}</td>
                    <td className="px-4 py-3 text-ink">
                      {row.diagram_file_name || "None"}
                    </td>
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

export default function NewQuestionImportPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preflight, setPreflight] =
    useState<QuestionImportPreflightResponse | null>(null);
  const [sources, setSources] = useState<QuestionSource[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSources() {
      try {
        setSources(await getQuestionSources());
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Unable to load question sources."
        );
      } finally {
        setIsLoadingSources(false);
      }
    }

    void loadSources();
  }, []);

  const selectedFileLabel = useMemo(() => {
    if (!file) {
      return "No file selected";
    }
    return `${file.name} (${Math.max(1, Math.round(file.size / 1024))} KB)`;
  }, [file]);

  function buildFormData(includeTitle: boolean) {
    const formData = new FormData();
    if (includeTitle) {
      formData.set("title", title.trim());
    }
    if (file) {
      formData.set("file", file);
    }
    if (source) {
      formData.set("source", source);
    }
    return formData;
  }

  function handleFileChange(selectedFile: File | null) {
    setFile(selectedFile);
    setPreflight(null);
    if (selectedFile && !isSupportedImportFile(selectedFile)) {
      setError("Only .csv and .zip files are supported.");
    } else {
      setError("");
    }
  }

  async function handleValidate() {
    setError("");

    if (!file) {
      setError("Choose a CSV or ZIP file to validate.");
      return;
    }

    if (!isSupportedImportFile(file)) {
      setError("Only .csv and .zip files are supported.");
      return;
    }

    setIsValidating(true);
    try {
      const report = await preflightQuestionImport(buildFormData(false));
      setPreflight(report);
    } catch (err) {
      setPreflight(null);
      setError(
        err instanceof ApiError ? err.message : "Unable to validate question file."
      );
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

    if (!title.trim()) {
      setError("Enter an import title.");
      return;
    }

    if (!file) {
      setError("Choose a CSV or ZIP file to import.");
      return;
    }

    if (!isSupportedImportFile(file)) {
      setError("Only .csv and .zip files are supported.");
      return;
    }

    setIsImporting(true);
    try {
      const batch = await createQuestionImport(buildFormData(true));
      router.push(`/admin/question-bank/imports/${batch.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to import question file."
      );
    } finally {
      setIsImporting(false);
    }
  }

  if (isLoadingSources) {
    return <LoadingState label="Preparing import form..." />;
  }

  if (error && !sources.length && isLoadingSources) {
    return <EmptyState title="Import form unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Import Questions"
        description="Validate a trusted JAMB or past-exam CSV/ZIP before importing draft questions."
        actions={
          <Link href="/admin/question-bank/imports">
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
            <Input
              label="Import title"
              data-testid="import-title-input"
              value={title}
              placeholder="JAMB Mathematics 2024"
              required
              onChange={(event) => setTitle(event.target.value)}
            />
            <Select
              label="Existing source"
              value={source}
              options={[
                { value: "", label: "Use source columns from CSV" },
                ...sources.map((item) => ({
                  value: String(item.id),
                  label: item.year ? `${item.name} (${item.year})` : item.name
                }))
              ]}
              onChange={(event) => {
                setSource(event.target.value);
                setPreflight(null);
              }}
            />
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-ink">
                Import file
              </span>
              <input
                type="file"
                data-testid="import-file-input"
                accept=".csv,.zip,text/csv,application/zip,application/x-zip-compressed"
                required
                className="block w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink file:mr-4 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-brand-700"
                onChange={(event) =>
                  handleFileChange(event.target.files?.[0] ?? null)
                }
              />
              <span className="mt-2 block text-xs text-muted">
                {selectedFileLabel}
              </span>
              <span className="mt-1 block text-xs text-muted">
                Upload a single questions.csv file, or a ZIP containing
                questions.csv and a diagrams/ folder.
              </span>
            </label>
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                variant="secondary"
                data-testid="import-validate-button"
                isLoading={isValidating}
                disabled={!file || isImporting}
                onClick={handleValidate}
              >
                Validate File
              </Button>
              <Button
                type="button"
                data-testid="import-now-button"
                isLoading={isImporting}
                disabled={!preflight?.can_import || isValidating}
                onClick={handleImport}
              >
                Import Now
              </Button>
              <CsvTemplateDownloadButton />
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">CSV Requirements</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Subject, class level, and topic must already exist. Imported questions
            stay as drafts until approved.
          </p>
          <p className="mt-2 text-sm leading-6 text-muted">
            CSV import: upload a single{" "}
            <span className="font-semibold text-ink">questions.csv</span> file.
            Use <span className="font-semibold text-ink">diagram_url</span> for
            hosted diagram images in normal CSV imports.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {requiredColumns.map((column) => (
              <span
                key={column}
                className="rounded-md bg-surface px-2 py-1 text-xs font-semibold text-muted"
              >
                {column}
              </span>
            ))}
          </div>
          <h3 className="mt-5 text-sm font-semibold text-ink">
            Optional diagram columns
          </h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {optionalDiagramColumns.map((column) => (
              <span
                key={column}
                className="rounded-md bg-brand-50 px-2 py-1 text-xs font-semibold text-brand-700"
              >
                {column}
              </span>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-muted">
            Questions with diagrams still import as drafts and must be reviewed
            before assignment or practice use.
          </p>
        </Card>

        <Card className="lg:col-start-2">
          <h2 className="text-base font-semibold text-ink">ZIP Diagram Guide</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            ZIP import: upload an archive with root-level questions.csv and a
            diagrams/ folder. Put images inside diagrams/ and use
            diagram_file_name in the CSV to match them.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-md bg-surface p-3 text-xs leading-6 text-ink">
{`questions.csv
diagrams/
  math_2024_q1.png
  math_2024_q2.jpg`}
          </pre>
          <p className="mt-4 text-sm leading-6 text-muted">
            Supported image types: png, jpg, jpeg, webp. Matched images are
            attached to imported draft questions. Missing images create row
            warnings and mark the question for manual review.
          </p>
        </Card>
      </div>

      {preflight ? <PreflightReport report={preflight} /> : null}
    </>
  );
}
