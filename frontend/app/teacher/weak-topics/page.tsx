"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getTeacherWeakTopics } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { TeacherWeakTopic } from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function formatPercentage(value: number) {
  return `${Number(value).toFixed(2)}%`;
}

function scoreTone(percentage: number): BadgeTone {
  if (percentage >= 70) {
    return "success";
  }

  if (percentage >= 50) {
    return "warning";
  }

  return "danger";
}

function scoreLabel(percentage: number) {
  if (percentage >= 70) {
    return "strong";
  }

  if (percentage >= 50) {
    return "average";
  }

  return "weak";
}

export default function TeacherWeakTopicsPage() {
  const [topics, setTopics] = useState<TeacherWeakTopic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWeakTopics() {
      try {
        setTopics(await getTeacherWeakTopics());
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Unable to load weak topics."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadWeakTopics();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading weak topics..." />;
  }

  if (error) {
    return <EmptyState title="Weak topics unavailable" description={error} />;
  }

  const totalSubmissions = topics.reduce(
    (total, topic) => total + topic.total_submissions,
    0
  );
  const weakStudentSignals = topics.reduce(
    (total, topic) => total + topic.weak_student_count,
    0
  );

  return (
    <>
      <PageHeader
        title="Weak Topics"
        description="Find topics that need reteaching, reinforcement, or targeted practice."
      />

      {topics.length ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Weak topics" value={topics.length} />
            <StatCard label="Submissions reviewed" value={totalSubmissions} />
            <StatCard label="Weak student signals" value={weakStudentSignals} />
            <StatCard
              label="Lowest topic average"
              value={formatPercentage(
                Math.min(...topics.map((topic) => topic.average_percentage))
              )}
            />
          </section>

          <section className="mt-6">
            <DataTable<TeacherWeakTopic>
              data={topics}
              columns={[
                {
                  key: "subject",
                  header: "Subject"
                },
                {
                  key: "topic",
                  header: "Topic",
                  render: (row) => (
                    <span className="block min-w-[14rem] font-semibold">
                      {row.topic}
                    </span>
                  )
                },
                {
                  key: "class_arm",
                  header: "Class arm"
                },
                {
                  key: "average_percentage",
                  header: "Average",
                  render: (row) => (
                    <div className="flex min-w-[8rem] flex-wrap items-center gap-2">
                      <span>{formatPercentage(row.average_percentage)}</span>
                      <Badge tone={scoreTone(row.average_percentage)}>
                        {scoreLabel(row.average_percentage)}
                      </Badge>
                    </div>
                  )
                },
                {
                  key: "total_submissions",
                  header: "Submissions"
                },
                {
                  key: "weak_student_count",
                  header: "Weak students"
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
          title="No weak topics detected yet."
          description="Topics that need reteaching will appear here after graded submissions exist."
        />
      )}
    </>
  );
}
