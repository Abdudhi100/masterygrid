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
import { getTeacherDashboard } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type {
  RemediationTopicCard,
  TeacherDashboard,
  TeacherDashboardAssignment,
  TeacherDashboardIntervention,
  TeacherDashboardNotification,
  TeacherDashboardQuickAction,
  TeacherDashboardRecentSubmission,
  TeacherWeakStudent,
  TeacherWeakTopic
} from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

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

function humanize(value?: string | null) {
  if (!value) {
    return "None";
  }
  return value.replaceAll("_", " ");
}

function statusTone(status: string): BadgeTone {
  if (["published", "open", "graded", "submitted", "resolved"].includes(status)) {
    return "success";
  }
  if (["draft", "due_soon", "late_open", "in_progress", "medium"].includes(status)) {
    return "warning";
  }
  if (["overdue", "urgent", "high", "closed", "archived"].includes(status)) {
    return "danger";
  }
  if (["normal", "low", "scheduled"].includes(status)) {
    return "brand";
  }
  return "neutral";
}

function AssignmentAlert({ assignment }: { assignment: TeacherDashboardAssignment }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold text-ink">{assignment.title}</p>
            <Badge tone={statusTone(assignment.deadline_status)}>
              {humanize(assignment.deadline_status)}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted">
            {assignment.subject} - {assignment.topic} - {assignment.class_arm}
          </p>
          <p className="mt-1 text-xs text-muted">
            Due {formatDate(assignment.due_at)} -{" "}
            {assignment.submitted_count}/{assignment.expected_students} submitted
          </p>
        </div>
        <Badge tone={statusTone(assignment.status)}>{assignment.status}</Badge>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Badge
          tone={
            assignment.submission_rate >= 80
              ? "success"
              : assignment.submission_rate >= 60
                ? "warning"
                : "danger"
          }
        >
          {formatPercentage(assignment.submission_rate)} submitted
        </Badge>
        <Link href={assignment.results_href}>
          <Button variant="secondary">View Results</Button>
        </Link>
      </div>
    </div>
  );
}

function SubmissionRow({
  submission
}: {
  submission: TeacherDashboardRecentSubmission;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-ink">{submission.student_name}</p>
          {submission.is_late ? <Badge tone="warning">Late</Badge> : null}
        </div>
        <p className="mt-1 text-sm text-muted">{submission.assignment_title}</p>
        <p className="mt-1 text-xs text-muted">
          Submitted {formatDate(submission.submitted_at)}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={statusTone(submission.status)}>{submission.status}</Badge>
        <span className="text-sm font-semibold text-ink">
          {submission.score}/{submission.total_marks} -{" "}
          {formatPercentage(submission.percentage)}
        </span>
        <Link href={submission.results_href}>
          <Button variant="secondary">Results</Button>
        </Link>
      </div>
    </div>
  );
}

function WeakStudentRow({ student }: { student: TeacherWeakStudent }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{student.student_name}</p>
          <p className="mt-1 text-sm text-muted">
            {student.class_arm ?? "No class"} -{" "}
            {student.graded_submission_count} graded
          </p>
        </div>
        <Badge tone={statusTone(student.risk_level)}>
          {formatPercentage(student.average_percentage)}
        </Badge>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">{student.recommendation}</p>
      <Link
        href={`/teacher/students/${student.student_id}/progress-report`}
        className="mt-3 inline-block"
      >
        <Button variant="secondary">Progress Report</Button>
      </Link>
    </div>
  );
}

function WeakTopicRow({ topic }: { topic: TeacherWeakTopic }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{topic.topic}</p>
        <Badge tone={statusTone("high")}>
          {formatPercentage(topic.average_percentage)}
        </Badge>
      </div>
      <p className="mt-1 text-sm text-muted">
        {topic.subject} - {topic.class_arm} - {topic.total_submissions} submissions
      </p>
      <p className="mt-2 text-sm leading-6 text-muted">{topic.recommendation}</p>
    </div>
  );
}

function RemediationCard({ card }: { card: RemediationTopicCard }) {
  const params = new URLSearchParams({
    classArm: String(card.action_payload.class_arm),
    subject: String(card.action_payload.subject),
    topic: String(card.action_payload.topic),
    questionCount: String(card.action_payload.question_count),
    title: card.action_payload.title,
    instructions: card.action_payload.instructions,
    remedial: "true"
  });

  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{card.topic}</p>
        <Badge tone={statusTone(card.priority)}>{card.priority}</Badge>
      </div>
      <p className="mt-1 text-sm text-muted">
        {card.subject} - {card.class_arm}
      </p>
      <p className="mt-2 text-sm leading-6 text-muted">
        {card.recommended_action}
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Badge tone="warning">{formatPercentage(card.average_score)} avg</Badge>
        <Badge tone="brand">{card.available_approved_questions} questions</Badge>
        <Link href={`/teacher/assignments/new?${params.toString()}`}>
          <Button variant="secondary">Create Remedial Assignment</Button>
        </Link>
      </div>
    </div>
  );
}

function InterventionRow({
  intervention
}: {
  intervention: TeacherDashboardIntervention;
}) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{intervention.title}</p>
          <p className="mt-1 text-sm text-muted">{intervention.student_name}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={statusTone(intervention.priority)}>
            {intervention.priority}
          </Badge>
          <Badge tone={statusTone(intervention.status)}>
            {humanize(intervention.status)}
          </Badge>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted">
        Due {intervention.due_date ?? "not set"} - updated{" "}
        {formatDate(intervention.updated_at)}
      </p>
      <Link href={intervention.href} className="mt-3 inline-block">
        <Button variant="secondary">Open Intervention</Button>
      </Link>
    </div>
  );
}

function NotificationRow({
  notification
}: {
  notification: TeacherDashboardNotification;
}) {
  const content = (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{notification.title}</p>
        <Badge tone={statusTone(notification.priority)}>
          {notification.priority}
        </Badge>
      </div>
      <p className="mt-1 text-sm leading-6 text-muted">
        {notification.message || humanize(notification.notification_type)}
      </p>
      <p className="mt-1 text-xs text-muted">
        {formatDate(notification.created_at)}
      </p>
    </div>
  );

  return notification.target_url ? (
    <Link href={notification.target_url}>{content}</Link>
  ) : (
    content
  );
}

function QuickAction({ action }: { action: TeacherDashboardQuickAction }) {
  return (
    <Link
      href={action.href}
      data-testid="teacher-dashboard-quick-action"
      className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface p-3 transition hover:border-brand-200 hover:bg-brand-50/40"
    >
      <span className="text-sm font-semibold text-ink">{action.title}</span>
      <Badge tone={statusTone(action.priority)}>{action.priority}</Badge>
    </Link>
  );
}

export default function TeacherDashboardPage() {
  const [dashboard, setDashboard] = useState<TeacherDashboard | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setDashboard(await getTeacherDashboard());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load teacher dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading teacher action center..." />;
  }

  if (error) {
    return <EmptyState title="Dashboard unavailable" description={error} />;
  }

  if (!dashboard) {
    return (
      <EmptyState
        title="No dashboard data"
        description="Your teacher action center will appear once assignments and submissions exist."
      />
    );
  }

  return (
    <div data-testid="teacher-dashboard-page">
      <PageHeader
        title="Teacher dashboard"
        description="Track assignments, submissions, weak signals, remediation, interventions, and next actions."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/teacher/assignments/new">
              <Button>Create Assignment</Button>
            </Link>
            <Link href="/teacher/remediation">
              <Button variant="secondary">Remediation</Button>
            </Link>
            <Link href="/teacher/interventions">
              <Button variant="secondary">Interventions</Button>
            </Link>
          </div>
        }
      />

      <section
        data-testid="teacher-dashboard-summary"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
      >
        <StatCard
          label="Active assignments"
          value={dashboard.summary.active_assignments_count}
          helper={`${dashboard.summary.published_assignments_count} published`}
        />
        <StatCard
          label="Drafts"
          value={dashboard.summary.draft_assignments_count}
          helper="Ready to generate or publish"
        />
        <StatCard
          label="Overdue"
          value={dashboard.summary.overdue_assignments_count}
          helper="Deadline follow-up"
        />
        <StatCard
          label="Low submission"
          value={dashboard.summary.low_submission_assignments_count}
          helper="Below expected rate"
        />
        <StatCard
          label="Unread notifications"
          value={dashboard.summary.unread_notifications_count}
          helper="Recent updates"
        />
        <StatCard
          label="Weak students"
          value={dashboard.summary.weak_students_count}
          helper="Need support"
        />
        <StatCard
          label="Weak topics"
          value={dashboard.summary.weak_topics_count}
          helper="Reteach signals"
        />
        <StatCard
          label="Open interventions"
          value={dashboard.summary.open_interventions_count}
          helper="Assigned or created"
        />
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card data-testid="teacher-dashboard-assignment-alerts">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Assignment Alerts
              </h2>
              <p className="mt-1 text-sm text-muted">
                Overdue and low-submission assignments need the fastest action.
              </p>
            </div>
            <Link href="/teacher/results">
              <Button variant="secondary">Open Results</Button>
            </Link>
          </div>

          {dashboard.assignments.overdue_assignments.length ||
          dashboard.assignments.low_submission_assignments.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.assignments.overdue_assignments.map((assignment) => (
                <AssignmentAlert key={`overdue-${assignment.id}`} assignment={assignment} />
              ))}
              {dashboard.assignments.low_submission_assignments.map((assignment) => (
                <AssignmentAlert key={`low-${assignment.id}`} assignment={assignment} />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No assignment alerts"
                description="Overdue and low-submission assignments will appear here."
              />
            </div>
          )}
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">Recent Submissions</h2>
          {dashboard.submissions.recent_submissions.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.submissions.recent_submissions.map((submission) => (
                <SubmissionRow key={submission.id} submission={submission} />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Student submissions will appear here after assignment attempts.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="teacher-dashboard-weak-students">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">Weak Students</h2>
            <Link href="/teacher/weak-students">
              <Button variant="secondary">View All</Button>
            </Link>
          </div>
          {dashboard.weak_students.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.weak_students.slice(0, 4).map((student) => (
                <WeakStudentRow key={student.student_id} student={student} />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              No weak students detected from graded submissions yet.
            </p>
          )}
        </Card>

        <Card data-testid="teacher-dashboard-weak-topics">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">Weak Topics</h2>
            <Link href="/teacher/weak-topics">
              <Button variant="secondary">View All</Button>
            </Link>
          </div>
          {dashboard.weak_topics.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.weak_topics.slice(0, 4).map((topic) => (
                <WeakTopicRow
                  key={`${topic.subject}-${topic.topic}-${topic.class_arm}`}
                  topic={topic}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Topic risk signals will appear after graded submissions.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="teacher-dashboard-remediation">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Remediation Recommendations
              </h2>
              <p className="mt-1 text-sm text-muted">
                Suggested actions from recent assignment performance.
              </p>
            </div>
            <Link href="/teacher/remediation">
              <Button variant="secondary">Open Remediation</Button>
            </Link>
          </div>
          {dashboard.remediation.recommended_actions.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.remediation.recommended_actions.map((card) => (
                <RemediationCard
                  key={`${card.class_arm_id}-${card.subject_id}-${card.topic_id}`}
                  card={card}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              {dashboard.remediation.summary.message}
            </p>
          )}
        </Card>

        <Card data-testid="teacher-dashboard-interventions">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Intervention Follow-up
            </h2>
            <Link href="/teacher/interventions">
              <Button variant="secondary">View Interventions</Button>
            </Link>
          </div>
          {dashboard.interventions.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.interventions.map((intervention) => (
                <InterventionRow
                  key={intervention.id}
                  intervention={intervention}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Open interventions assigned to or created by you will appear here.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="teacher-dashboard-notifications">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">Notifications</h2>
            <Link href="/notifications">
              <Button variant="secondary">Open Inbox</Button>
            </Link>
          </div>
          {dashboard.notifications.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.notifications.map((notification) => (
                <NotificationRow
                  key={notification.id}
                  notification={notification}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              No unread notifications right now.
            </p>
          )}
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">Quick Actions</h2>
          <p className="mt-1 text-sm text-muted">
            Shortcuts based on your current assignment and student signals.
          </p>
          <div className="mt-4 space-y-3">
            {dashboard.quick_actions.map((action) => (
              <QuickAction key={`${action.title}-${action.href}`} action={action} />
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
