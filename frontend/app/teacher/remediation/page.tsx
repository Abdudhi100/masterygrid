"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { ApiError } from "@/lib/api";
import { getTeacherRemediationPlan } from "@/lib/analytics";
import type {
  RemediationTopicCard,
  TeacherRemediationPlan
} from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

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

function priorityTone(priority: RemediationTopicCard["priority"]): BadgeTone {
  if (priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  return "success";
}

function assignmentHref(card: RemediationTopicCard) {
  const params = new URLSearchParams({
    classArm: String(card.action_payload.class_arm),
    subject: String(card.action_payload.subject),
    topic: String(card.action_payload.topic),
    questionCount: String(card.action_payload.question_count),
    title: card.action_payload.title,
    instructions: card.action_payload.instructions,
    remedial: "true"
  });
  return `/teacher/assignments/new?${params.toString()}`;
}

function RemediationCard({ card }: { card: RemediationTopicCard }) {
  const canCreate = card.available_approved_questions > 0;

  return (
    <div
      data-testid="remediation-topic-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={priorityTone(card.priority)}>{card.priority} priority</Badge>
        <Badge tone={canCreate ? "success" : "warning"}>
          {card.available_approved_questions} approved questions
        </Badge>
      </div>

      <h3 className="mt-3 text-base font-semibold text-ink">{card.topic}</h3>
      <p className="mt-1 text-sm text-muted">
        {card.subject} - {card.class_arm}
      </p>

      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(card.average_score)}
          </p>
          <p className="text-muted">average score</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{card.attempted_count}</p>
          <p className="text-muted">attempts</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{card.weak_student_count}</p>
          <p className="text-muted">weak students</p>
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-muted">
        {card.recommended_action}
      </p>

      {card.affected_students.length ? (
        <div className="mt-4 rounded-md border border-line bg-white p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted">
            Affected students
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {card.affected_students.slice(0, 4).map((student) => (
              <Badge key={student.student_id} tone="neutral">
                {student.student_name} - {formatPercentage(student.average_score)}
              </Badge>
            ))}
            {card.affected_students.length > 4 ? (
              <Badge tone="neutral">+{card.affected_students.length - 4} more</Badge>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {canCreate ? (
          <Link href={assignmentHref(card)}>
            <Button data-testid="remediation-create-assignment-button">
              Create Remedial Assignment
            </Button>
          </Link>
        ) : (
          <Button disabled variant="secondary">
            Needs Approved Questions
          </Button>
        )}
        <span className="text-xs font-semibold text-muted">
          {card.recommended_question_count || "No"} recommended questions
        </span>
      </div>
    </div>
  );
}

export default function TeacherRemediationPage() {
  const [plan, setPlan] = useState<TeacherRemediationPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadPlan() {
      try {
        setPlan(await getTeacherRemediationPlan());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load remediation plan."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadPlan();
  }, []);

  const primaryAction = useMemo(
    () => plan?.recommended_actions[0] ?? null,
    [plan]
  );

  if (isLoading) {
    return <LoadingState label="Loading remediation plan..." />;
  }

  if (error) {
    return <EmptyState title="Remediation unavailable" description={error} />;
  }

  if (!plan) {
    return (
      <EmptyState
        title="No remediation plan"
        description="Remediation recommendations will appear after graded submissions exist."
      />
    );
  }

  return (
    <div data-testid="teacher-remediation-page">
      <PageHeader
        title="Remediation"
        description="Turn weak topic signals into targeted follow-up assignments."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/teacher/weak-topics">
              <Button variant="secondary">Weak Topics</Button>
            </Link>
            <Link href="/teacher/assignments/new">
              <Button variant="secondary">Create Assignment</Button>
            </Link>
          </div>
        }
      />

      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={primaryAction ? priorityTone(primaryAction.priority) : "neutral"}>
                {primaryAction ? `${primaryAction.priority} priority` : "monitoring"}
              </Badge>
              <Badge tone="brand">
                {plan.summary.actionable_topic_count} actionable
              </Badge>
            </div>
            <h2 className="mt-3 text-xl font-semibold text-ink">
              {plan.summary.message}
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Recommendations are computed from graded assignment submissions and
              approved active question-bank availability.
            </p>
          </div>
          {primaryAction ? (
            <Link href={assignmentHref(primaryAction)}>
              <Button data-testid="remediation-create-assignment-button">
                Create Remedial Assignment
              </Button>
            </Link>
          ) : null}
        </div>
      </Card>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Weak topics" value={plan.summary.total_weak_topics} />
        <StatCard
          label="Actionable topics"
          value={plan.summary.actionable_topic_count}
        />
        <StatCard
          label="Affected students"
          value={plan.summary.total_affected_students}
        />
        <StatCard
          label="Average weak-topic score"
          value={formatPercentage(plan.summary.average_score)}
        />
      </section>

      <section className="mt-6">
        <Card>
          <h2 className="text-base font-semibold text-ink">
            Recommended Actions
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Start with topics that have low scores, affected students, and enough
            approved questions for a short remedial assignment.
          </p>

          {plan.weak_topic_cards.length ? (
            <div className="mt-5 grid gap-4 xl:grid-cols-2">
              {plan.weak_topic_cards.map((card) => (
                <RemediationCard
                  key={`${card.class_arm_id}-${card.subject_id}-${card.topic_id}`}
                  card={card}
                />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No weak topics yet"
                description="Weak topic recommendations will appear after students submit assignments."
              />
            </div>
          )}
        </Card>
      </section>

      {plan.affected_students.length ? (
        <section className="mt-6">
          <Card>
            <h2 className="text-base font-semibold text-ink">
              Most Affected Students
            </h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {plan.affected_students.slice(0, 8).map((student) => (
                <div
                  key={`${student.student_id}-${student.topic_id}`}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <p className="font-semibold text-ink">{student.student_name}</p>
                  <p className="mt-1 text-sm text-muted">
                    {student.topic_title} - {formatPercentage(student.average_score)}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </section>
      ) : null}
    </div>
  );
}
