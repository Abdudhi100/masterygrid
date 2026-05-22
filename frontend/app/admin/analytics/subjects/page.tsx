"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminSubjectPerformance } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminSubjectPerformance } from "@/types/analytics";
import {
  formatPercentage,
  ScoreBadge,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

export default function AdminSubjectPerformancePage() {
  const [rows, setRows] = useState<AdminSubjectPerformance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRows() {
      try {
        setRows(await getAdminSubjectPerformance());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load subject performance."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadRows();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading subject performance..." />;
  }

  if (error) {
    return <EmptyState title="Subject performance unavailable" description={error} />;
  }

  const weakTopicTotal = rows.reduce(
    (total, row) => total + row.weak_topic_count,
    0
  );
  const highRiskCount = rows.filter((row) => row.risk_level === "high").length;

  return (
    <>
      <PageHeader
        title="Subject Performance"
        description="Track subject-level performance and weakest topics across the school."
      />

      {rows.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Subjects" value={rows.length} />
            <StatCard
              label="Assignments"
              value={rows.reduce((total, row) => total + row.total_assignments, 0)}
            />
            <StatCard label="Weak topics" value={weakTopicTotal} />
            <StatCard label="High-risk subjects" value={highRiskCount} />
          </section>

          <section className="mt-6">
            <DataTable<AdminSubjectPerformance>
              data={rows}
              columns={[
                {
                  key: "subject_name",
                  header: "Subject",
                  render: (row) => (
                    <span className="font-semibold">{row.subject_name}</span>
                  )
                },
                {
                  key: "total_assignments",
                  header: "Assignments"
                },
                {
                  key: "total_submissions",
                  header: "Submissions"
                },
                {
                  key: "average_percentage",
                  header: "Average",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.average_percentage)}</span>
                      <ScoreBadge percentage={row.average_percentage} />
                    </div>
                  )
                },
                {
                  key: "weak_topic_count",
                  header: "Weak topics"
                },
                {
                  key: "weakest_topics",
                  header: "Weakest topics",
                  render: (row) =>
                    row.weakest_topics.length ? (
                      <div className="min-w-[14rem] space-y-1">
                        {row.weakest_topics.map((topic) => (
                          <p key={topic.topic} className="text-sm text-ink">
                            {topic.topic} -{" "}
                            {formatPercentage(topic.average_percentage)}
                          </p>
                        ))}
                      </div>
                    ) : (
                      "No weak topics"
                    )
                },
                {
                  key: "risk_level",
                  header: "Risk",
                  render: (row) => <StatusBadge value={row.risk_level} />
                },
                {
                  key: "recommendation",
                  header: "Recommendation",
                  render: (row) => (
                    <span className="block min-w-[18rem] max-w-lg leading-6">
                      {row.recommendation}
                    </span>
                  )
                }
              ]}
            />
          </section>
        </>
      ) : (
        <EmptyState
          title="No subject performance yet"
          description="Subject analytics will appear after assignments and submissions exist."
        />
      )}
    </>
  );
}
