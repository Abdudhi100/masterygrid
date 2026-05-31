"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { ApiError } from "@/lib/api";
import { getPracticeLearningPath } from "@/lib/practice";
import type {
  LearningPathCategory,
  LearningPathTopicCard,
  PracticeRecommendationPriority,
  StudentLearningPath
} from "@/types/practice";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not practised";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not practised";
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

function priorityTone(priority: PracticeRecommendationPriority): BadgeTone {
  if (priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  return "success";
}

function categoryLabel(category: LearningPathCategory) {
  if (category === "weak_topic") {
    return "Weak Topic";
  }
  if (category === "needs_reinforcement") {
    return "Needs Reinforcement";
  }
  if (category === "new_topic") {
    return "New Topic";
  }
  return "Challenge";
}

function categoryTone(category: LearningPathCategory): BadgeTone {
  if (category === "weak_topic") {
    return "danger";
  }
  if (category === "needs_reinforcement") {
    return "warning";
  }
  if (category === "new_topic") {
    return "brand";
  }
  return "success";
}

function practiceHref(card: LearningPathTopicCard) {
  const params = new URLSearchParams({
    subject: String(card.action_payload.subject),
    topic: String(card.action_payload.topic),
    difficulty: card.action_payload.difficulty,
    question_count: String(card.action_payload.question_count)
  });

  if (card.action_payload.class_level) {
    params.set("class_level", String(card.action_payload.class_level));
  }

  return `/student/practice?${params.toString()}`;
}

function LearningPathCard({ card }: { card: LearningPathTopicCard }) {
  return (
    <div
      data-testid="learning-path-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="neutral">Step {card.rank}</Badge>
        <Badge tone={categoryTone(card.category)}>
          {categoryLabel(card.category)}
        </Badge>
        <Badge tone={priorityTone(card.priority)}>{card.priority}</Badge>
      </div>

      <div className="mt-3">
        <h3 className="text-base font-semibold text-ink">{card.topic_title}</h3>
        <p className="mt-1 text-sm text-muted">
          {card.subject_name}
          {card.class_level_name ? ` - ${card.class_level_name}` : ""}
        </p>
      </div>

      <p className="mt-3 text-sm leading-6 text-muted">{card.reason}</p>

      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(card.performance.average_percentage)}
          </p>
          <p className="text-muted">average</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {card.performance.questions_answered}
          </p>
          <p className="text-muted">answered</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {card.available_question_count}
          </p>
          <p className="text-muted">available</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Badge tone="brand">{humanize(card.difficulty)}</Badge>
        <span className="text-xs font-semibold text-muted">
          {card.recommended_question_count} recommended questions
        </span>
        <span className="text-xs text-muted">
          Last practised {formatDate(card.performance.last_practiced_at)}
        </span>
      </div>

      <Link href={practiceHref(card)} className="mt-4 inline-block">
        <Button data-testid="learning-path-start-button">
          Start Recommended Practice
        </Button>
      </Link>
    </div>
  );
}

export default function StudentLearningPathPage() {
  const [learningPath, setLearningPath] = useState<StudentLearningPath | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLearningPath() {
      try {
        setLearningPath(await getPracticeLearningPath());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load your learning path."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadLearningPath();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading learning path..." />;
  }

  if (error) {
    return <EmptyState title="Learning path unavailable" description={error} />;
  }

  if (!learningPath) {
    return (
      <EmptyState
        title="No learning path yet"
        description="Your learning path will appear when approved practice questions are available."
      />
    );
  }

  const nextAction = learningPath.recommended_next_action;

  return (
    <div data-testid="learning-path-dashboard">
      <PageHeader
        title="Learning Path"
        description="Follow the next best practice steps from your submitted work and approved question-bank topics."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/student/practice">
              <Button variant="secondary">Practice</Button>
            </Link>
            <Link href="/student/practice/analytics">
              <Button variant="secondary">Practice Analytics</Button>
            </Link>
          </div>
        }
      />

      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={nextAction ? categoryTone(nextAction.category) : "neutral"}>
                {humanize(learningPath.overall_status)}
              </Badge>
              {nextAction ? (
                <Badge tone={priorityTone(nextAction.priority)}>
                  {nextAction.priority} priority
                </Badge>
              ) : null}
            </div>
            <h2 className="mt-3 text-xl font-semibold text-ink">
              {learningPath.headline}
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              {learningPath.message}
            </p>
          </div>
          {nextAction ? (
            <Link href={practiceHref(nextAction)}>
              <Button data-testid="learning-path-primary-start-button">
                Start Recommended Practice
              </Button>
            </Link>
          ) : null}
        </div>
      </Card>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Sessions completed"
          value={learningPath.summary.total_sessions_completed}
        />
        <StatCard
          label="Questions answered"
          value={learningPath.summary.total_questions_answered}
        />
        <StatCard
          label="Practice average"
          value={formatPercentage(
            learningPath.summary.overall_average_percentage
          )}
        />
        <StatCard
          label="Last practice"
          value={formatDate(learningPath.summary.last_practice_at)}
        />
      </section>

      {nextAction ? (
        <section className="mt-6">
          <Card>
            <h2 className="text-base font-semibold text-ink">
              Recommended Next Action
            </h2>
            <div className="mt-4">
              <LearningPathCard card={nextAction} />
            </div>
          </Card>
        </section>
      ) : null}

      <section className="mt-6">
        <Card>
          <h2 className="text-base font-semibold text-ink">Topic Path</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Work through these cards in order. The list updates after you submit
            practice sessions.
          </p>

          {learningPath.topic_cards.length ? (
            <div className="mt-5 grid gap-4 xl:grid-cols-2">
              {learningPath.topic_cards.map((card) => (
                <LearningPathCard
                  key={`${card.rank}-${card.subject_id}-${card.topic_id}`}
                  card={card}
                />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No approved practice questions"
                description="Ask your teacher or school admin to approve question-bank questions for your subjects."
              />
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
