"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  formatDate,
  formatPercentage,
  humanize
} from "@/app/admin/analytics/_components/analyticsUi";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminDashboard } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import { isDemoModeEnabled } from "@/lib/demoMode";
import type {
  AdminAssignmentCompliance,
  AdminClassPerformance,
  AdminDashboard,
  AdminDashboardAuditLog,
  AdminDashboardIntervention,
  AdminDashboardNotification,
  AdminDashboardQuickAction,
  AdminSubjectPerformance,
  AdminTeacherActivity,
  AdminWeakStudent
} from "@/types/analytics";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function toneFor(value?: string | null): BadgeTone {
  if (!value) {
    return "neutral";
  }

  if (
    [
      "critical",
      "urgent",
      "high",
      "poor",
      "inactive",
      "overdue",
      "closed",
      "archived"
    ].includes(value)
  ) {
    return "danger";
  }

  if (
    [
      "moderate",
      "medium",
      "warning",
      "low_activity",
      "in_progress",
      "due_soon",
      "late_open"
    ].includes(value)
  ) {
    return "warning";
  }

  if (["low", "good", "active", "complete", "published"].includes(value)) {
    return "success";
  }

  if (["normal", "draft", "scheduled"].includes(value)) {
    return "brand";
  }

  return "neutral";
}

function SectionTitle({
  title,
  href,
  action
}: {
  title: string;
  href?: string;
  action?: string;
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {href && action ? (
        <Link href={href}>
          <Button variant="secondary">{action}</Button>
        </Link>
      ) : null}
    </div>
  );
}

function ClassRiskRow({ row }: { row: AdminClassPerformance }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{row.class_arm_name}</p>
          <p className="mt-1 text-sm text-muted">
            {row.class_level} - {row.total_students} students
          </p>
        </div>
        <Badge tone={toneFor(row.risk_level)}>{humanize(row.risk_level)}</Badge>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Badge tone={toneFor(row.risk_level)}>
          {formatPercentage(row.average_percentage)} avg
        </Badge>
        <Badge tone={row.submission_rate >= 80 ? "success" : "warning"}>
          {formatPercentage(row.submission_rate)} submitted
        </Badge>
        <Badge tone="brand">{row.weak_student_count} weak students</Badge>
      </div>
    </div>
  );
}

function SubjectRiskRow({ row }: { row: AdminSubjectPerformance }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{row.subject_name}</p>
          <p className="mt-1 text-sm text-muted">
            {row.total_assignments} assignments - {row.total_submissions} submissions
          </p>
        </div>
        <Badge tone={toneFor(row.risk_level)}>{humanize(row.risk_level)}</Badge>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">{row.recommendation}</p>
    </div>
  );
}

function WeakStudentRow({ student }: { student: AdminWeakStudent }) {
  return (
    <Link
      href={`/admin/students/${student.student_id}/progress-report`}
      className="block rounded-md border border-line bg-surface p-3 transition hover:border-brand-200 hover:bg-brand-50/40"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{student.student_name}</p>
          <p className="mt-1 text-sm text-muted">
            {student.class_arm ?? "Class not set"} -{" "}
            {student.graded_submission_count} graded
          </p>
        </div>
        <Badge tone={toneFor(student.risk_level)}>
          {formatPercentage(student.average_percentage)}
        </Badge>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">{student.recommendation}</p>
    </Link>
  );
}

function ComplianceRow({ assignment }: { assignment: AdminAssignmentCompliance }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{assignment.title}</p>
          <p className="mt-1 text-sm text-muted">
            {assignment.teacher_name} - {assignment.class_arm}
          </p>
          <p className="mt-1 text-xs text-muted">
            Due {formatDate(assignment.due_at)}
          </p>
        </div>
        <Badge tone={toneFor(assignment.deadline_status)}>
          {humanize(assignment.deadline_status)}
        </Badge>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Badge tone={toneFor(assignment.compliance_status)}>
          {formatPercentage(assignment.submission_rate)} submitted
        </Badge>
        <Badge tone="brand">{assignment.not_started_count} not started</Badge>
        <Badge tone="neutral">{assignment.late_submission_count} late</Badge>
      </div>
    </div>
  );
}

function InterventionRow({
  intervention
}: {
  intervention: AdminDashboardIntervention;
}) {
  return (
    <Link
      href={intervention.href}
      className="block rounded-md border border-line bg-surface p-3 transition hover:border-brand-200 hover:bg-brand-50/40"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{intervention.title}</p>
          <p className="mt-1 text-sm text-muted">
            {intervention.student_name} - {intervention.class_arm ?? "No class"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={toneFor(intervention.priority)}>
            {humanize(intervention.priority)}
          </Badge>
          <Badge tone={toneFor(intervention.status)}>
            {humanize(intervention.status)}
          </Badge>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted">
        Due {intervention.due_date ?? "not set"} - updated{" "}
        {formatDate(intervention.updated_at)}
      </p>
    </Link>
  );
}

function TeacherRow({ teacher }: { teacher: AdminTeacherActivity }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink">{teacher.teacher_name}</p>
          <p className="mt-1 text-sm text-muted">
            {teacher.assigned_classes_count} classes -{" "}
            {teacher.assigned_subjects_count} subjects
          </p>
        </div>
        <Badge tone={toneFor(teacher.activity_status)}>
          {humanize(teacher.activity_status)}
        </Badge>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">
        {teacher.recommendation}
      </p>
    </div>
  );
}

function NotificationRow({
  notification
}: {
  notification: AdminDashboardNotification;
}) {
  const content = (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{notification.title}</p>
        <Badge tone={toneFor(notification.priority)}>
          {humanize(notification.priority)}
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

function AuditRow({ log }: { log: AdminDashboardAuditLog }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-ink">{humanize(log.action)}</p>
        <Badge tone="brand">{humanize(log.category)}</Badge>
      </div>
      <p className="mt-1 text-sm text-muted">
        {log.actor_email || "system"} - {log.object_repr || log.object_type}
      </p>
      <p className="mt-1 text-xs text-muted">{formatDate(log.created_at)}</p>
    </div>
  );
}

function QuickAction({ action }: { action: AdminDashboardQuickAction }) {
  return (
    <Link
      href={action.href}
      data-testid="admin-dashboard-quick-action"
      className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface p-3 transition hover:border-brand-200 hover:bg-brand-50/40"
    >
      <span className="text-sm font-semibold text-ink">{action.title}</span>
      <Badge tone={toneFor(action.priority)}>{humanize(action.priority)}</Badge>
    </Link>
  );
}

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setDashboard(await getAdminDashboard());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load admin dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="School dashboard"
          description="A whole-school command center for setup, academic risk, compliance, interventions, notifications, and audit activity."
        />
        <LoadingState label="Loading school command center..." />
      </>
    );
  }

  if (error) {
    return (
      <>
        <PageHeader
          title="School dashboard"
          description="A whole-school command center for setup, academic risk, compliance, interventions, notifications, and audit activity."
        />
        <ErrorState
          title="Dashboard unavailable"
          description={error}
          dashboardHref="/admin/dashboard"
        />
      </>
    );
  }

  if (!dashboard) {
    return (
      <>
        <PageHeader
          title="School dashboard"
          description="A whole-school command center for setup, academic risk, compliance, interventions, notifications, and audit activity."
        />
        <EmptyState
          title="No dashboard data"
          description="School analytics will appear once onboarding, assignments, and submissions exist."
        />
      </>
    );
  }

  const assignmentAlerts = [
    ...dashboard.compliance.overdue_assignments,
    ...dashboard.compliance.low_submission_assignments
  ].filter(
    (assignment, index, rows) =>
      rows.findIndex((row) => row.assignment_id === assignment.assignment_id) ===
      index
  );

  return (
    <div data-testid="admin-dashboard-page">
      <PageHeader
        title="School dashboard"
        description="A whole-school command center for setup, academic risk, compliance, interventions, notifications, and audit activity."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/setup">
              <Button>Setup Wizard</Button>
            </Link>
            <Link href="/admin/interventions">
              <Button variant="secondary">Interventions</Button>
            </Link>
            <Link href="/admin/analytics">
              <Button variant="secondary">Analytics</Button>
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
        data-testid="admin-dashboard-summary"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <StatCard
          label="Setup"
          value={`${dashboard.summary.setup_completion_percentage}%`}
          helper={
            dashboard.setup.is_setup_complete
              ? "Onboarding complete"
              : "Continue onboarding"
          }
        />
        <StatCard
          label="Students"
          value={dashboard.summary.students_count}
          helper={`${dashboard.summary.teachers_count} teachers`}
        />
        <StatCard
          label="Classes"
          value={dashboard.summary.class_arms_count}
          helper={`${dashboard.summary.subjects_count} subjects`}
        />
        <StatCard
          label="Published assignments"
          value={dashboard.summary.published_assignments_count}
          helper={`${dashboard.summary.overdue_assignments_count} overdue`}
        />
        <StatCard
          label="Submission rate"
          value={formatPercentage(dashboard.summary.assignment_submission_rate)}
          helper="Across published assignments"
        />
        <StatCard
          label="Weak students"
          value={dashboard.summary.weak_students_count}
          helper="Need academic support"
        />
        <StatCard
          label="High-risk classes"
          value={dashboard.summary.high_risk_classes_count}
          helper="Priority class support"
        />
        <StatCard
          label="Open interventions"
          value={dashboard.summary.open_interventions_count}
          helper={`${dashboard.summary.unread_notifications_count} unread notifications`}
        />
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
        <Card data-testid="admin-dashboard-setup">
          <SectionTitle title="Setup Progress" href="/admin/setup" action="Open Setup" />
          <div className="mt-4">
            <div className="h-3 overflow-hidden rounded-full bg-slate-100">
              <div
                data-testid="admin-dashboard-setup-progress"
                className="h-full rounded-full bg-brand-600"
                style={{
                  width: `${dashboard.setup.completion_percentage}%`
                }}
              />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge
                tone={
                  dashboard.setup.is_setup_complete ? "success" : "warning"
                }
              >
                {dashboard.setup.completion_percentage}% complete
              </Badge>
              <Badge
                tone={
                  dashboard.setup.is_setup_complete ? "success" : "brand"
                }
              >
                {dashboard.setup.is_setup_complete ? "complete" : "in progress"}
              </Badge>
            </div>
            <p className="mt-4 text-sm leading-6 text-muted">
              {dashboard.setup.next_step
                ? dashboard.setup.next_step.recommendation
                : "All required onboarding steps are complete."}
            </p>
          </div>
        </Card>

        <Card data-testid="admin-dashboard-quick-actions">
          <h2 className="text-base font-semibold text-ink">Quick Actions</h2>
          <p className="mt-1 text-sm text-muted">
            Shortcuts based on the school&apos;s current setup, compliance, and risk signals.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {dashboard.quick_actions.map((action) => (
              <QuickAction key={`${action.title}-${action.href}`} action={action} />
            ))}
          </div>
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-3">
        <Card data-testid="admin-dashboard-risk-overview">
          <SectionTitle
            title="High-Risk Classes"
            href="/admin/analytics/classes"
            action="View Classes"
          />
          {dashboard.performance.weakest_classes.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.performance.weakest_classes.slice(0, 4).map((row) => (
                <ClassRiskRow key={row.class_arm_id} row={row} />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Class risk signals will appear after assignments and submissions.
            </p>
          )}
        </Card>

        <Card>
          <SectionTitle
            title="Weak Subjects"
            href="/admin/analytics/subjects"
            action="View Subjects"
          />
          {dashboard.performance.weakest_subjects.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.performance.weakest_subjects.slice(0, 4).map((row) => (
                <SubjectRiskRow key={row.subject_id} row={row} />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Subject risk signals will appear after graded submissions.
            </p>
          )}
        </Card>

        <Card>
          <SectionTitle
            title="Weak Students"
            href="/admin/analytics/weak-students"
            action="View Students"
          />
          {dashboard.performance.weak_students_preview.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.performance.weak_students_preview
                .slice(0, 4)
                .map((student) => (
                  <WeakStudentRow key={student.student_id} student={student} />
                ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              No weak students detected from graded submissions yet.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card data-testid="admin-dashboard-compliance">
          <SectionTitle
            title="Assignment Compliance"
            href="/admin/analytics/compliance"
            action="Open Compliance"
          />
          {assignmentAlerts.length ? (
            <div className="mt-4 space-y-3">
              {assignmentAlerts.slice(0, 5).map((assignment) => (
                <ComplianceRow
                  key={assignment.assignment_id}
                  assignment={assignment}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Overdue and low-submission assignments will appear here.
            </p>
          )}
        </Card>

        <Card data-testid="admin-dashboard-interventions">
          <SectionTitle
            title="Intervention Follow-up"
            href="/admin/interventions"
            action="Open Interventions"
          />
          {dashboard.interventions.open_interventions.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.interventions.open_interventions.map((intervention) => (
                <InterventionRow
                  key={intervention.id}
                  intervention={intervention}
                />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Open intervention records will appear here.
            </p>
          )}
        </Card>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-3">
        <Card data-testid="admin-dashboard-teachers">
          <SectionTitle
            title="Teacher Follow-up"
            href="/admin/analytics/teachers"
            action="View Teachers"
          />
          {dashboard.teachers.teacher_activity_preview.length ? (
            <div className="mt-4 space-y-3">
              {(dashboard.teachers.teachers_needing_followup.length
                ? dashboard.teachers.teachers_needing_followup
                : dashboard.teachers.teacher_activity_preview
              )
                .slice(0, 4)
                .map((teacher) => (
                  <TeacherRow key={teacher.teacher_id} teacher={teacher} />
                ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Teacher activity appears after teachers create assignments.
            </p>
          )}
        </Card>

        <Card data-testid="admin-dashboard-notifications">
          <SectionTitle
            title="Notifications"
            href="/notifications"
            action="Open Inbox"
          />
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

        <Card data-testid="admin-dashboard-audit">
          <SectionTitle
            title="Recent Audit Activity"
            href="/admin/audit-logs"
            action="Open Logs"
          />
          {dashboard.audit.recent_audit_logs.length ? (
            <div className="mt-4 space-y-3">
              {dashboard.audit.recent_audit_logs.map((log) => (
                <AuditRow key={log.id} log={log} />
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted">
              Audit activity will appear as users take important actions.
            </p>
          )}
        </Card>
      </section>
    </div>
  );
}
