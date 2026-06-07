"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { ApiError } from "@/lib/api";
import { getStudentDashboard } from "@/lib/analytics";
import { isDemoModeEnabled } from "@/lib/demoMode";
import type {
  StudentDashboard,
  StudentDashboardAssignment,
  StudentDashboardNotification,
  StudentDashboardQuickAction,
  StudentDashboardRecentResult
} from "@/types/analytics";
import type { LearningPathTopicCard } from "@/types/practice";

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

function formatDate(value?: string | null) {
  if (!value) {
    return "No date";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "No date";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function humanize(value?: string | null) {
  if (!value) {
    return "Not started";
  }
  return value.replaceAll("_", " ");
}

function deadlineTone(status: string): BadgeTone {
  if (status === "overdue") {
    return "danger";
  }
  if (status === "late_open" || status === "due_soon") {
    return "warning";
  }
  if (status === "submitted" || status === "graded") {
    return "success";
  }
  if (status === "scheduled") {
    return "brand";
  }
  return "neutral";
}

function priorityTone(priority: string): BadgeTone {
  if (priority === "urgent" || priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  if (priority === "low" || priority === "normal") {
    return "brand";
  }
  return "neutral";
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

function AssignmentRow({ assignment }: { assignment: StudentDashboardAssignment }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-ink">{assignment.title}</p>
          <Badge tone={deadlineTone(assignment.deadline_status)}>
            {humanize(assignment.deadline_status)}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-muted">
          {assignment.subject_name} - {assignment.topic_title} -{" "}
          {assignment.question_count} questions
        </p>
        <p className="mt-1 text-xs text-muted">
          Due {formatDate(assignment.due_at)}
          {assignment.allow_late_submissions
            ? ` - late until ${formatDate(assignment.late_submission_deadline)}`
            : ""}
        </p>
      </div>
      <Link href={assignment.href}>
        <Button variant="secondary">
          {assignment.submission_status === "in_progress" ? "Continue" : "Open"}
        </Button>
      </Link>
    </div>
  );
}

function RecentResultRow({ result }: { result: StudentDashboardRecentResult }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-ink">{result.assignment_title}</p>
          {result.is_late ? <Badge tone="warning">Late</Badge> : null}
        </div>
        <p className="mt-1 text-sm text-muted">
          {result.subject_name} - {result.topic_title}
        </p>
        <p className="mt-1 text-xs text-muted">
          Graded {formatDate(result.graded_at)}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm font-semibold text-ink">
          {result.score}/{result.total_marks} -{" "}
          {formatPercentage(result.percentage)}
        </p>
        <Link href={result.href}>
          <Button variant="secondary">Result</Button>
        </Link>
      </div>
    </div>
  );
}

function NotificationRow({
  notification
}: {
  notification: StudentDashboardNotification;
}) {
  const content = (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{notification.title}</p>
        <Badge tone={priorityTone(notification.priority)}>
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

function QuickAction({ action }: { action: StudentDashboardQuickAction }) {
  return (
    <Link
      href={action.href}
      data-testid="student-dashboard-quick-action"
      className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface p-3 transition hover:border-brand-200 hover:bg-brand-50/40"
    >
      <span className="text-sm font-semibold text-ink">{action.title}</span>
      <Badge tone={priorityTone(action.priority)}>{action.priority}</Badge>
    </Link>
  );
}

export default function StudentDashboardPage() {
  const [dashboard, setDashboard] = useState<StudentDashboard | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setDashboard(await getStudentDashboard());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load student dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading your learning home..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Dashboard unavailable"
        description={error}
        dashboardHref="/student/dashboard"
      />
    );
  }

  if (!dashboard) {
    return (
      <ErrorState
        title="Dashboard unavailable"
        description="Your learning dashboard could not be loaded."
        dashboardHref="/student/dashboard"
      />
    );
  }

  const urgentAssignments = [
    ...dashboard.assignments.overdue,
    ...dashboard.assignments.due_soon
  ];
  const nextAction =
    dashboard.learning_path.recommended_next_action ??
    dashboard.learning_path.top_topic_card;

  return (
    <div data-testid="student-dashboard-page">
      <PageHeader
        title="Student dashboard"
        description="Your assignments, practice progress, learning path, and next actions in one place."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/student/assignments">
              <Button variant="secondary">My Assignments</Button>
            </Link>
            <Link href="/student/practice">
              <Button>Start Practice</Button>
            </Link>
            <Link href="/student/learning-path">
              <Button variant="secondary">Learning Path</Button>
            </Link>
            {isDemoModeEnabled ? (
              <Link href="/demo-guide">
                <Button variant="secondary">Open Demo Guide</Button>
              </Link>
            ) : null}
          </div>
        }
      />

      <section
        data-testid="student-dashboard-summary"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <StatCard
          label="Pending assignments"
          value={dashboard.summary.pending_assignments_count}
          helper={`${dashboard.summary.due_soon_assignments_count} due soon`}
        />
        <StatCard
          label="Overdue"
          value={dashboard.summary.overdue_assignments_count}
          helper="Needs attention"
        />
        <StatCard
          label="Assignment average"
          value={formatPercentage(dashboard.summary.assignment_average)}
          helper={`${dashboard.summary.graded_assignments_count} graded`}
        />
        <StatCard
          label="Practice average"
          value={formatPercentage(dashboard.summary.practice_average)}
          helper={`${dashboard.summary.practice_sessions_count} sessions`}
        />
        <StatCard
          label="Unread notifications"
          value={dashboard.summary.unread_notifications_count}
          helper="Latest school updates"
        />
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card data-testid="student-dashboard-urgent-assignments">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Urgent Assignments
              </h2>
              <p className="mt-1 text-sm text-muted">
                Overdue and due-soon work is shown first.
              </p>
            </div>
            <Link href="/student/assignments">
              <Button variant="secondary">View All</Button>
            </Link>
          </div>

          {urgentAssignments.length ? (
            <div className="mt-4 space-y-3">
              {urgentAssignments.slice(0, 5).map((assignment) => (
                <AssignmentRow key={assignment.id} assignment={assignment} />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No urgent assignments"
                description="Assignments that are overdue or due soon will appear here."
              />
            </div>
          )}
        </Card>

        <Card data-testid="student-dashboard-learning-path">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={nextAction ? priorityTone(nextAction.priority) : "neutral"}>
              {humanize(dashboard.learning_path.overall_status)}
            </Badge>
            {nextAction ? (
              <Badge tone="brand">{humanize(nextAction.category)}</Badge>
            ) : null}
          </div>
          <h2 className="mt-3 text-base font-semibold text-ink">
            {dashboard.learning_path.headline}
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            {dashboard.learning_path.message}
          </p>

          {nextAction ? (
            <div className="mt-4 rounded-md border border-line bg-surface p-3">
              <p className="font-semibold text-ink">{nextAction.topic_title}</p>
              <p className="mt-1 text-sm text-muted">
                {nextAction.subject_name}
                {nextAction.class_level_name
                  ? ` - ${nextAction.class_level_name}`
                  : ""}
              </p>
              <p className="mt-2 text-sm leading-6 text-muted">
                {nextAction.reason}
              </p>
              <Link href={practiceHref(nextAction)} className="mt-3 inline-block">
                <Button>Start Recommended Practice</Button>
              </Link>
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Approved practice questions will unlock a personalized learning
              path.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="student-dashboard-practice-summary">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Practice Summary
              </h2>
              <p className="mt-1 text-sm text-muted">
                Recent practice and improvement areas from approved questions.
              </p>
            </div>
            <Link href="/student/practice/analytics">
              <Button variant="secondary">Analytics</Button>
            </Link>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-line bg-surface p-3">
              <p className="text-sm text-muted">Weak topics</p>
              <p className="mt-2 text-2xl font-semibold text-ink">
                {dashboard.practice.weak_topics.length}
              </p>
            </div>
            <div className="rounded-md border border-line bg-surface p-3">
              <p className="text-sm text-muted">Strong topics</p>
              <p className="mt-2 text-2xl font-semibold text-ink">
                {dashboard.practice.strong_topics.length}
              </p>
            </div>
          </div>

          {dashboard.practice.weak_topics.length ? (
            <div className="mt-4 space-y-2">
              {dashboard.practice.weak_topics.slice(0, 3).map((topic) => (
                <div
                  key={topic.topic_id}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <p className="font-semibold text-ink">{topic.topic_title}</p>
                  <p className="mt-1 text-sm text-muted">
                    {topic.subject_name} -{" "}
                    {formatPercentage(topic.average_percentage)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Complete a practice session to reveal weak and strong topics.
            </p>
          )}
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">Recent Results</h2>
          {dashboard.assignments.recently_graded.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.assignments.recently_graded.map((result) => (
                <RecentResultRow
                  key={result.submission_id}
                  result={result}
                />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No graded assignments yet"
                description="Your recent scores will appear after submitted assignments are graded."
              />
            </div>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="student-dashboard-notifications">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">
                Notifications
              </h2>
              <p className="mt-1 text-sm text-muted">
                Your latest unread updates.
              </p>
            </div>
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
            Shortcuts based on your current workload and learning path.
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
