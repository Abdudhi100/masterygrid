"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/layout/PageHeader";
import { CsvTemplateDownloadButton } from "@/components/question-bank/CsvTemplateDownloadButton";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import { createQuestionImport, getQuestionSources } from "@/lib/questionBank";
import type { QuestionSource } from "@/types/questionBank";

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

function isSupportedImportFile(file: File) {
  const name = file.name.toLowerCase();
  return name.endsWith(".csv") || name.endsWith(".zip");
}

export default function NewQuestionImportPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sources, setSources] = useState<QuestionSource[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

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

    const formData = new FormData();
    formData.set("title", title.trim());
    formData.set("file", file);
    if (source) {
      formData.set("source", source);
    }

    setIsSubmitting(true);
    try {
      const batch = await createQuestionImport(formData);
      router.push(`/admin/question-bank/imports/${batch.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to import question file."
      );
    } finally {
      setIsSubmitting(false);
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
        description="Upload a trusted JAMB or past-exam CSV or ZIP. Imported questions are saved as drafts for review."
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
          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Import title"
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
              onChange={(event) => setSource(event.target.value)}
            />
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-ink">
                Import file
              </span>
              <input
                type="file"
                accept=".csv,.zip,text/csv,application/zip,application/x-zip-compressed"
                required
                className="block w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink file:mr-4 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-brand-700"
                onChange={(event) => {
                  const selectedFile = event.target.files?.[0] ?? null;
                  setFile(selectedFile);
                  if (selectedFile && !isSupportedImportFile(selectedFile)) {
                    setError("Only .csv and .zip files are supported.");
                  } else {
                    setError("");
                  }
                }}
              />
              <span className="mt-2 block text-xs text-muted">
                Upload a single questions.csv file, or a ZIP containing
                questions.csv and a diagrams/ folder.
              </span>
            </label>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" isLoading={isSubmitting}>
                Upload Import
              </Button>
              <CsvTemplateDownloadButton />
            </div>
          </form>
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
    </>
  );
}
