"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  QuestionDifficultyBadge,
  QuestionStatusBadge
} from "@/components/question-bank/QuestionBadges";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import {
  archiveQuestion,
  bulkQuestionAction,
  getQuestionQualityDashboard,
  rejectQuestion
} from "@/lib/questionBank";
import type {
  QuestionQualityDashboard,
  QuestionQualityIssueType,
  QuestionQualityRow
} from "@/types/questionBank";

type Tone = "neutral" | "success" | "warning" | "danger" | "brand";

const tabs: Array<{
  key: QuestionQualityIssueType;
  label: string;
}> = [
  { key: "needs_manual_review", label: "Needs Review" },
  { key: "missing_explanations", label: "Missing Explanations" },
  { key: "diagram_issues", label: "Diagram Issues" },
  { key: "duplicate_suspects", label: "Duplicates" },
  { key: "imported_drafts", label: "Imported Drafts" },
  { key: "ready_for_approval", label: "Ready for Approval" },
  { key: "metadata_issues", label: "Metadata Issues" }
];

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

function issueTone(issueType: string): Tone {
  if (issueType === "ready_for_approval") {
    return "success";
  }
  if (issueType === "duplicate_suspect" || issueType === "imported_draft") {
    return "warning";
  }
  return "danger";
}

function truncate(value: string, limit = 160) {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit)}...`;
}

export default function QuestionQualityDashboardPage() {
  const [dashboard, setDashboard] = useState<QuestionQualityDashboard | null>(null);
  const [activeTab, setActiveTab] =
    useState<QuestionQualityIssueType>("needs_manual_review");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isBulkApproving, setIsBulkApproving] = useState(false);
  const [loadingActionId, setLoadingActionId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    try {
      const payload = await getQuestionQualityDashboard({ limit: 50 });
      setDashboard(payload);
      setError("");
      if (!payload.sections[activeTab]?.length) {
        const firstPopulatedTab = tabs.find((tab) => payload.sections[tab.key].length);
        if (firstPopulatedTab) {
          setActiveTab(firstPopulatedTab.key);
        }
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load question quality dashboard."
      );
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const rows = useMemo(
    () => dashboard?.sections[activeTab] ?? [],
    [activeTab, dashboard]
  );

  function toggleSelection(id: number) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  }

  async function runRowAction(
    row: QuestionQualityRow,
    action: "reject" | "archive"
  ) {
    setError("");
    setSuccess("");
    setLoadingActionId(row.id);
    try {
      if (action === "reject") {
        await rejectQuestion(row.id);
        setSuccess("Question rejected.");
      } else {
        await archiveQuestion(row.id);
        setSuccess("Question archived.");
      }
      setSelectedIds((current) => current.filter((id) => id !== row.id));
      await loadDashboard();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to update question.");
    } finally {
      setLoadingActionId(null);
    }
  }

  async function runBulkApprove() {
    setError("");
    setSuccess("");
    setIsBulkApproving(true);
    try {
      const result = await bulkQuestionAction(selectedIds, "approve");
      const failed = result.results.filter((item) => item.status === "failed");
      if (failed.length) {
        setError(
          `${failed.length} question(s) could not be approved. ${failed
            .slice(0, 2)
            .map((item) => item.message)
            .join(" ")}`
        );
      } else {
        setSuccess(`${result.results.length} question(s) approved.`);
      }
      setSelectedIds([]);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to bulk approve.");
    } finally {
      setIsBulkApproving(false);
    }
  }

  if (isLoading && !dashboard) {
    return <LoadingState label="Loading question quality dashboard..." />;
  }

  if (error && !dashboard) {
    return <EmptyState title="Question quality unavailable" description={error} />;
  }

  if (!dashboard) {
    return (
      <EmptyState
        title="No quality data"
        description="Question quality data could not be loaded."
      />
    );
  }

  const summary = dashboard.summary;

  return (
    <>
      <PageHeader
        title="Question Quality"
        description="Review imported drafts, diagram issues, duplicate suspects, and draft questions ready for approval."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/question-bank/imports">
              <Button variant="secondary">Import History</Button>
            </Link>
            <Link href="/admin/question-bank">
              <Button variant="secondary">Question Bank</Button>
            </Link>
          </div>
        }
      />

      {success ? (
        <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-success">
          {success}
        </div>
      ) : null}
      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <section
        className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
        data-testid="question-quality-summary"
      >
        <SummaryCard label="Total Questions" value={summary.total_questions} />
        <SummaryCard label="Drafts" value={summary.draft_count} tone="warning" />
        <SummaryCard
          label="Needs Review"
          value={summary.needs_manual_review_count}
          tone={summary.needs_manual_review_count ? "danger" : "neutral"}
        />
        <SummaryCard
          label="Diagram Issues"
          value={summary.diagram_issue_count}
          tone={summary.diagram_issue_count ? "danger" : "neutral"}
        />
        <SummaryCard
          label="Ready"
          value={summary.ready_for_review_count}
          tone="success"
        />
      </section>

      <Card className="mb-6" data-testid="question-quality-dashboard">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => {
            const count = dashboard.sections[tab.key].length;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                data-testid="question-quality-tab"
                className={`rounded-md border px-3 py-2 text-sm font-semibold transition ${
                  isActive
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-line bg-white text-muted hover:border-brand-200"
                }`}
                onClick={() => {
                  setActiveTab(tab.key);
                  setSelectedIds([]);
                }}
              >
                {tab.label}
                <span className="ml-2 text-xs">({count})</span>
              </button>
            );
          })}
        </div>
      </Card>

      {activeTab === "ready_for_approval" && rows.length ? (
        <Card className="mb-4 border-emerald-100 bg-emerald-50">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm leading-6 text-muted">
              Select ready draft questions and approve them in one batch. Each
              question is still validated individually.
            </p>
            <Button
              data-testid="question-quality-bulk-action"
              disabled={!selectedIds.length}
              isLoading={isBulkApproving}
              onClick={runBulkApprove}
            >
              Bulk Approve Selected
            </Button>
          </div>
        </Card>
      ) : null}

      {!rows.length ? (
        <EmptyState
          title="No questions in this section"
          description="There are no question bank items matching this quality category."
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-line bg-white">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-line text-sm">
              <thead className="bg-surface">
                <tr>
                  {[
                    activeTab === "ready_for_approval" ? "Select" : "",
                    "Question",
                    "Issue",
                    "Subject",
                    "Topic",
                    "Difficulty",
                    "Status",
                    "Source",
                    "Media",
                    "Created",
                    "Actions"
                  ].map((heading, index) => (
                    <th
                      key={`${heading}-${index}`}
                      className="px-4 py-3 text-left font-semibold text-muted"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {rows.map((row) => (
                  <tr
                    key={`${activeTab}-${row.id}-${row.issue_type}`}
                    data-testid="question-quality-row"
                    className="align-top hover:bg-surface"
                  >
                    <td className="px-4 py-3">
                      {activeTab === "ready_for_approval" ? (
                        <input
                          type="checkbox"
                          aria-label={`Select question ${row.id}`}
                          checked={selectedIds.includes(row.id)}
                          onChange={() => toggleSelection(row.id)}
                        />
                      ) : null}
                    </td>
                    <td className="min-w-[22rem] px-4 py-3 text-ink">
                      {truncate(row.question_preview)}
                      <div className="mt-2 flex flex-wrap gap-2">
                        {row.has_diagram ? <Badge tone="brand">diagram</Badge> : null}
                        {row.needs_manual_review ? (
                          <Badge tone="warning">manual review</Badge>
                        ) : null}
                      </div>
                    </td>
                    <td className="min-w-[14rem] px-4 py-3">
                      <div className="space-y-2">
                        <Badge
                          data-testid="question-quality-issue-badge"
                          tone={issueTone(row.issue_type)}
                        >
                          {row.issue_type.replaceAll("_", " ")}
                        </Badge>
                        <p className="leading-6 text-muted">{row.issue_message}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-ink">
                      {row.subject_name || "Not set"}
                    </td>
                    <td className="px-4 py-3 text-ink">
                      {row.topic_title || "Not set"}
                    </td>
                    <td className="px-4 py-3">
                      {row.difficulty ? (
                        <QuestionDifficultyBadge difficulty={row.difficulty} />
                      ) : (
                        "Not set"
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <QuestionStatusBadge status={row.status} />
                    </td>
                    <td className="px-4 py-3 text-ink">
                      {row.source_name || "No source"}
                      {row.import_batch_id ? (
                        <p className="mt-1 text-xs text-muted">
                          Import: {row.import_batch_title || row.import_batch_id}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-ink">{row.media_count}</td>
                    <td className="px-4 py-3 text-ink">
                      {formatDate(row.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex min-w-[13rem] flex-wrap gap-2">
                        <Link
                          href={`/admin/question-bank/${row.id}`}
                          data-testid="question-quality-view-link"
                        >
                          <Button variant="secondary">View</Button>
                        </Link>
                        <Button
                          variant="secondary"
                          isLoading={loadingActionId === row.id}
                          onClick={() => runRowAction(row, "reject")}
                        >
                          Reject
                        </Button>
                        <Button
                          variant="ghost"
                          isLoading={loadingActionId === row.id}
                          onClick={() => runRowAction(row, "archive")}
                        >
                          Archive
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
