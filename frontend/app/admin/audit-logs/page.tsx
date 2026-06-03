"use client";

import { Fragment, FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getAuditLogs } from "@/lib/audit";
import type { AuditCategory, AuditLog, AuditLogFilters } from "@/types/audit";

const categories: Array<{ label: string; value: AuditCategory | "" }> = [
  { label: "All categories", value: "" },
  { label: "Auth", value: "auth" },
  { label: "Academics", value: "academics" },
  { label: "Question Bank", value: "question_bank" },
  { label: "Assignment", value: "assignment" },
  { label: "Submission", value: "submission" },
  { label: "Intervention", value: "intervention" },
  { label: "Notification", value: "notification" },
  { label: "Import", value: "import" },
  { label: "User Management", value: "user_management" },
  { label: "System", value: "system" }
];

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function categoryTone(category: AuditCategory) {
  if (category === "question_bank" || category === "assignment") {
    return "brand";
  }
  if (category === "intervention" || category === "import") {
    return "warning";
  }
  if (category === "system") {
    return "neutral";
  }
  return "success";
}

function metadataSummary(metadata: Record<string, unknown>) {
  const keys = Object.keys(metadata);
  if (!keys.length) {
    return "No metadata";
  }
  return keys.slice(0, 4).join(", ");
}

function actorLabel(log: AuditLog) {
  return log.actor_name || log.actor_email || "System";
}

function targetLabel(log: AuditLog) {
  return log.target_user_name || log.target_user_email || "";
}

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [category, setCategory] = useState<AuditCategory | "">("");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLogs() {
      setIsLoading(true);
      try {
        const payload = await getAuditLogs(filters);
        setLogs(payload.results);
        setTotalCount(payload.count);
        setError("");
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Unable to load audit logs."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadLogs();
  }, [filters]);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setExpandedId(null);
    setFilters({
      category,
      search: search.trim()
    });
  }

  return (
    <div data-testid="audit-logs-page">
      <PageHeader
        title="Audit Logs"
        description="Review important system activity, including user changes, imports, question reviews, assignments, submissions, and interventions."
      />

      <Card className="mb-6">
        <form
          className="grid gap-4 lg:grid-cols-[16rem_1fr_auto]"
          onSubmit={applyFilters}
        >
          <label className="space-y-2">
            <span className="text-sm font-medium text-muted">Category</span>
            <select
              data-testid="audit-log-filter-category"
              className="min-h-11 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              value={category}
              onChange={(event) =>
                setCategory(event.target.value as AuditCategory | "")
              }
            >
              {categories.map((item) => (
                <option key={item.value || "all"} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-muted">Search</span>
            <input
              data-testid="audit-log-search-input"
              className="min-h-11 w-full rounded-md border border-line px-3 py-2 text-sm text-ink outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search actor, action, object, or target user"
            />
          </label>

          <div className="flex items-end">
            <Button type="submit">Apply Filters</Button>
          </div>
        </form>
      </Card>

      {isLoading ? <LoadingState label="Loading audit logs..." /> : null}

      {error && !isLoading ? (
        <EmptyState title="Audit logs unavailable" description={error} />
      ) : null}

      {!isLoading && !error && !logs.length ? (
        <EmptyState
          title="No audit logs found"
          description="Important activity will appear here after users perform auditable actions."
        />
      ) : null}

      {!isLoading && !error && logs.length ? (
        <Card>
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">Recent activity</h2>
            <p className="text-sm text-muted">
              Showing {logs.length} of {totalCount} log(s)
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-line text-sm">
              <thead className="bg-surface">
                <tr>
                  {[
                    "Date",
                    "Actor",
                    "Action",
                    "Category",
                    "Object",
                    "Target User",
                    "School",
                    "Details"
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
                {logs.map((log) => (
                  <Fragment key={log.id}>
                    <tr
                      data-testid="audit-log-row"
                      className="align-top hover:bg-surface"
                    >
                      <td className="min-w-40 px-4 py-3 text-ink">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="min-w-52 px-4 py-3">
                        <p className="font-medium text-ink">{actorLabel(log)}</p>
                        <p className="mt-1 text-xs text-muted">
                          {log.actor_role || "system"}
                        </p>
                      </td>
                      <td className="min-w-48 px-4 py-3 font-medium text-ink">
                        {formatLabel(log.action)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={categoryTone(log.category)}>
                          {formatLabel(log.category)}
                        </Badge>
                      </td>
                      <td className="min-w-56 px-4 py-3 text-ink">
                        <p>{log.object_repr || log.object_type || "Not set"}</p>
                        <p className="mt-1 text-xs text-muted">
                          {log.object_type}
                          {log.object_id ? ` #${log.object_id}` : ""}
                        </p>
                      </td>
                      <td className="min-w-52 px-4 py-3 text-ink">
                        {targetLabel(log) || "None"}
                      </td>
                      <td className="min-w-40 px-4 py-3 text-ink">
                        {log.school_name || "Global"}
                      </td>
                      <td className="min-w-48 px-4 py-3">
                        <p className="mb-2 text-xs text-muted">
                          {metadataSummary(log.metadata)}
                        </p>
                        <Button
                          type="button"
                          variant="secondary"
                          data-testid="audit-log-metadata-toggle"
                          onClick={() =>
                            setExpandedId((current) =>
                              current === log.id ? null : log.id
                            )
                          }
                        >
                          {expandedId === log.id ? "Hide" : "View"}
                        </Button>
                      </td>
                    </tr>
                    {expandedId === log.id ? (
                      <tr className="bg-surface">
                        <td colSpan={8} className="px-4 py-3">
                          <pre className="max-h-72 overflow-auto rounded-md bg-white p-3 text-xs leading-6 text-ink">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
