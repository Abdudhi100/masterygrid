"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { ApiError } from "@/lib/api";
import { getPracticeAnalyticsDashboard } from "@/lib/practice";
import type {
  PracticeAnalyticsDashboard,
  PracticeRecommendation,
  PracticeRecommendationPriority,
  PracticeTopicPerformance,
  PracticeTopicStrength
} from "@/types/practice";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatPercentage(value?: number | string | null) {
  if (value === null || value === undefined || value === "") {
    return "Not scored";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "Not scored";
  }

  return `${numeric.toFixed(2)}%`;
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function strengthTone(value: PracticeTopicStrength): BadgeTone {
  if (value === "strong") {
    return "success";
  }
  if (value === "average") {
    return "warning";
  }
  return "danger";
}

function priorityTone(value: PracticeRecommendationPriority): BadgeTone {
  if (value === "high") {
    return "danger";
  }
  if (value === "medium") {
    return "warning";
  }
  return "success";
}

function recommendationHref(recommendation: PracticeRecommendation) {
  const params = new URLSearchParams({
    subject: String(recommendation.subject_id),
    topic: String(recommendation.topic_id),
    difficulty: recommendation.recommended_difficulty,
    question_count: String(recommendation.suggested_question_count)
  });
  return `/student/practice?${params.toString()}`;
}

function topicPracticeHref(topic: PracticeTopicPerformance) {
  const params = new URLSearchParams({
    subject: String(topic.subject_id),
    topic: String(topic.topic_id),
    difficulty: topic.average_percentage !== null && topic.average_percentage < 50
      ? "easy"
      : "mixed",
    question_count: "10"
  });
  return `/student/practice?${params.toString()}`;
}

export default function StudentPracticeAnalyticsPage() {
  const [dashboard, setDashboard] = useState<PracticeAnalyticsDashboard | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setDashboard(await getPracticeAnalyticsDashboard());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load practice analytics."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const recommendationByTopic = useMemo(() => {
    const rows = new Map<number, PracticeRecommendation>();
    dashboard?.recommendations.forEach((recommendation) => {
      rows.set(recommendation.topic_id, recommendation);
    });
    return rows;
  }, [dashboard]);

  if (isLoading) {
    return <LoadingState label="Loading practice analytics..." />;
  }

  if (error) {
    return <EmptyState title="Practice analytics unavailable" description={error} />;
  }

  if (!dashboard) {
    return (
      <EmptyState
        title="No practice analytics"
        description="Complete a practice session to unlock personalized analytics."
      />
    );
  }

  const { summary } = dashboard;

  return (
    <div data-testid="practice-analytics-dashboard">
      <PageHeader
        title="Practice Analytics"
        description="Review your practice performance and choose what to work on next."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/student/practice">
              <Button variant="secondary">Back to Practice</Button>
            </Link>
            <Link href="/student/learning-path">
              <Button variant="secondary">Learning Path</Button>
            </Link>
            <Link href="/student/practice#start-practice">
              <Button>Start Practice</Button>
            </Link>
          </div>
        }
      />

      {dashboard.message ? (
        <Card className="mb-6 border-brand-100 bg-brand-50">
          <p className="text-sm font-semibold text-brand-700">
            {dashboard.message}
          </p>
          <p className="mt-2 text-sm leading-6 text-brand-700">
            Recommendations can still suggest topics when approved questions are
            available.
          </p>
        </Card>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <StatCard
          label="Sessions completed"
          value={summary.total_sessions_completed}
        />
        <StatCard
          label="Questions answered"
          value={summary.total_questions_answered}
        />
        <StatCard
          label="Correct answers"
          value={summary.total_correct_answers}
        />
        <StatCard
          label="Overall average"
          value={formatPercentage(summary.overall_average_percentage)}
        />
        <StatCard
          label="Best percentage"
          value={formatPercentage(summary.best_percentage)}
        />
        <StatCard
          label="Lowest percentage"
          value={formatPercentage(summary.lowest_percentage)}
        />
        <StatCard
          label="Last practice"
          value={formatDate(summary.last_practice_at)}
        />
        <StatCard
          label="Best subject"
          value={summary.best_subject ?? "Not available"}
        />
        <StatCard
          label="Weakest subject"
          value={summary.weakest_subject ?? "Not available"}
        />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink">Weak Topics</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Topics below 50% with enough practice evidence appear here.
          </p>
          <div className="mt-4">
            <DataTable<PracticeTopicPerformance>
              data={dashboard.weak_topics}
              emptyTitle="No weak topics yet"
              emptyDescription="Complete more practice sessions to identify weak areas."
              columns={[
                {
                  key: "topic_title",
                  header: "Topic",
                  render: (topic) => (
                    <div>
                      <p className="font-semibold text-ink">
                        {topic.topic_title}
                      </p>
                      <p className="mt-1 text-xs text-muted">
                        {topic.subject_name}
                      </p>
                    </div>
                  )
                },
                {
                  key: "average_percentage",
                  header: "Average",
                  render: (topic) => (
                    <div className="flex flex-wrap items-center gap-2">
                      <span>{formatPercentage(topic.average_percentage)}</span>
                      <Badge tone={strengthTone(topic.strength_level)}>
                        {topic.strength_level}
                      </Badge>
                    </div>
                  )
                },
                {
                  key: "questions_answered",
                  header: "Questions",
                  render: (topic) => String(topic.questions_answered)
                },
                {
                  key: "sessions_completed",
                  header: "Sessions",
                  render: (topic) => String(topic.sessions_completed)
                },
                {
                  key: "recommendation",
                  header: "Recommendation",
                  render: (topic) =>
                    recommendationByTopic.get(topic.topic_id)?.reason ??
                    "Practise this topic again with easier questions first."
                },
                {
                  key: "action",
                  header: "Action",
                  render: (topic) => (
                    <Link href={topicPracticeHref(topic)}>
                      <Button variant="secondary">Practise Topic</Button>
                    </Link>
                  )
                }
              ]}
            />
          </div>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">Strong Topics</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Topics where your practice average is 70% or higher.
          </p>
          <div className="mt-4">
            <DataTable<PracticeTopicPerformance>
              data={dashboard.strong_topics}
              emptyTitle="No strong topics yet"
              emptyDescription="Strong topics will appear after successful practice sessions."
              columns={[
                {
                  key: "topic_title",
                  header: "Topic",
                  render: (topic) => (
                    <div>
                      <p className="font-semibold text-ink">
                        {topic.topic_title}
                      </p>
                      <p className="mt-1 text-xs text-muted">
                        {topic.subject_name}
                      </p>
                    </div>
                  )
                },
                {
                  key: "average_percentage",
                  header: "Average",
                  render: (topic) => (
                    <div className="flex flex-wrap items-center gap-2">
                      <span>{formatPercentage(topic.average_percentage)}</span>
                      <Badge tone={strengthTone(topic.strength_level)}>
                        {topic.strength_level}
                      </Badge>
                    </div>
                  )
                },
                {
                  key: "questions_answered",
                  header: "Questions",
                  render: (topic) => String(topic.questions_answered)
                },
                {
                  key: "sessions_completed",
                  header: "Sessions",
                  render: (topic) => String(topic.sessions_completed)
                }
              ]}
            />
          </div>
        </Card>
      </section>

      <section id="recommendations" className="mt-6">
        <Card>
          <h2 className="text-base font-semibold text-ink">Recommendations</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            These are based on your submitted practice results and available
            approved question-bank questions.
          </p>

          {dashboard.recommendations.length ? (
            <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {dashboard.recommendations.map((recommendation) => (
                <div
                  key={`${recommendation.subject_id}-${recommendation.topic_id}`}
                  className="rounded-md border border-line bg-surface p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Badge tone={priorityTone(recommendation.priority)}>
                      {recommendation.priority}
                    </Badge>
                    <Badge tone="brand">
                      {humanize(recommendation.recommended_difficulty)}
                    </Badge>
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-ink">
                    {recommendation.topic_title}
                  </h3>
                  <p className="mt-1 text-sm text-muted">
                    {recommendation.subject_name}
                  </p>
                  <p className="mt-3 min-h-12 text-sm leading-6 text-muted">
                    {recommendation.reason}
                  </p>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="font-semibold text-ink">
                        {recommendation.available_question_count}
                      </p>
                      <p className="text-muted">available</p>
                    </div>
                    <div>
                      <p className="font-semibold text-ink">
                        {recommendation.suggested_question_count}
                      </p>
                      <p className="text-muted">suggested</p>
                    </div>
                  </div>
                  <Link
                    href={recommendationHref(recommendation)}
                    className="mt-4 inline-block"
                  >
                    <Button>Start Practice</Button>
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No recommendations yet"
                description="Recommendations need either practice history or approved questions in the question bank."
              />
            </div>
          )}
        </Card>
      </section>

      <section className="mt-6" data-testid="practice-recent-sessions">
        <Card>
          <h2 className="text-base font-semibold text-ink">Recent Practice</h2>
          <div className="mt-4">
            <DataTable
              data={dashboard.recent_sessions}
              emptyTitle="No recent practice"
              emptyDescription="Submitted practice sessions will appear here."
              columns={[
                {
                  key: "subject_name",
                  header: "Subject",
                  render: (session) => session.subject_name
                },
                {
                  key: "topic_title",
                  header: "Topic",
                  render: (session) => session.topic_title ?? "Any topic"
                },
                {
                  key: "difficulty",
                  header: "Difficulty",
                  render: (session) => humanize(session.difficulty)
                },
                {
                  key: "score",
                  header: "Score",
                  render: (session) =>
                    `${session.score}/${session.total_marks}`
                },
                {
                  key: "percentage",
                  header: "Percentage",
                  render: (session) => formatPercentage(session.percentage)
                },
                {
                  key: "submitted_at",
                  header: "Submitted",
                  render: (session) => formatDate(session.submitted_at)
                },
                {
                  key: "action",
                  header: "Action",
                  render: (session) => (
                    <Link href={`/student/practice/${session.id}/result`}>
                      <Button variant="secondary">View Result</Button>
                    </Link>
                  )
                }
              ]}
            />
          </div>
        </Card>
      </section>
    </div>
  );
}
