"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { InterventionManagementPage } from "@/components/interventions/InterventionManagementPage";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminInterventionDashboard } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type {
  AdminAssignmentComplianceAlert,
  AdminClassIntervention,
  AdminInterventionActionPayload,
  AdminInterventionDashboard,
  AdminSubjectIntervention,
  AdminTeacherIntervention,
  AdminUrgentIntervention,
  AdminWeakStudentCluster,
  InterventionRiskLevel
} from "@/types/analytics";
import { formatPercentage } from "@/app/admin/analytics/_components/analyticsUi";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

function riskTone(risk: InterventionRiskLevel): BadgeTone {
  if (risk === "critical" || risk === "high") {
    return "danger";
  }
  if (risk === "moderate") {
    return "warning";
  }
  return "success";
}

function riskLabel(risk: InterventionRiskLevel) {
  return risk.charAt(0).toUpperCase() + risk.slice(1);
}

function ActionLink({ action }: { action: AdminInterventionActionPayload }) {
  return (
    <Link href={action.href} data-testid="intervention-action-link">
      <Button variant="secondary">{action.label}</Button>
    </Link>
  );
}

function RiskBadge({ risk }: { risk: InterventionRiskLevel }) {
  return <Badge tone={riskTone(risk)}>{riskLabel(risk)}</Badge>;
}

function UrgentCard({ item }: { item: AdminUrgentIntervention }) {
  return (
    <div className="rounded-md border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        <RiskBadge risk={item.risk_level} />
        <Badge tone="neutral">{item.category.replaceAll("_", " ")}</Badge>
      </div>
      <h3 className="mt-3 text-base font-semibold text-ink">{item.title}</h3>
      <p className="mt-2 text-sm leading-6 text-muted">{item.description}</p>
      <p className="mt-3 text-sm leading-6 text-ink">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function ClassCard({ item }: { item: AdminClassIntervention }) {
  return (
    <div
      data-testid="class-intervention-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-ink">{item.class_arm_name}</h3>
          <p className="mt-1 text-sm text-muted">{item.class_level}</p>
        </div>
        <RiskBadge risk={item.risk_level} />
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.average_score)}
          </p>
          <p className="text-muted">average</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{item.submitted_count}</p>
          <p className="text-muted">submissions</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{item.weak_student_count}</p>
          <p className="text-muted">weak students</p>
        </div>
      </div>
      {item.main_weak_topics.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {item.main_weak_topics.map((topic) => (
            <Badge key={`${topic.subject}-${topic.topic}`} tone="warning">
              {topic.topic}
            </Badge>
          ))}
        </div>
      ) : null}
      <p className="mt-4 text-sm leading-6 text-muted">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function SubjectCard({ item }: { item: AdminSubjectIntervention }) {
  return (
    <div
      data-testid="subject-intervention-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-ink">{item.subject_name}</h3>
        <RiskBadge risk={item.risk_level} />
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.average_score)}
          </p>
          <p className="text-muted">average</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{item.weak_student_count}</p>
          <p className="text-muted">weak students</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{item.weak_class_count}</p>
          <p className="text-muted">affected classes</p>
        </div>
      </div>
      {item.affected_class_arms.length ? (
        <p className="mt-3 text-sm text-muted">
          {item.affected_class_arms.slice(0, 3).join(", ")}
        </p>
      ) : null}
      <p className="mt-4 text-sm leading-6 text-muted">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function TeacherCard({ item }: { item: AdminTeacherIntervention }) {
  return (
    <div
      data-testid="teacher-intervention-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-ink">{item.teacher_name}</h3>
          <p className="mt-1 text-sm text-muted">{item.teacher_email}</p>
        </div>
        <RiskBadge risk={item.risk_level} />
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">{item.assignment_count}</p>
          <p className="text-muted">assignments</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.average_class_score)}
          </p>
          <p className="text-muted">class score</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.submission_rate)}
          </p>
          <p className="text-muted">submission rate</p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-muted">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function WeakClusterCard({ item }: { item: AdminWeakStudentCluster }) {
  return (
    <div
      data-testid="weak-student-cluster-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-ink">{item.topic}</h3>
          <p className="mt-1 text-sm text-muted">
            {item.subject} - {item.class_arm}
          </p>
        </div>
        <RiskBadge risk={item.risk_level} />
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <p className="font-semibold text-ink">{item.weak_student_count}</p>
          <p className="text-muted">weak students</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.average_score)}
          </p>
          <p className="text-muted">cluster average</p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-muted">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function ComplianceCard({ item }: { item: AdminAssignmentComplianceAlert }) {
  return (
    <div
      data-testid="compliance-alert-card"
      className="rounded-md border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-ink">{item.title}</h3>
          <p className="mt-1 text-sm text-muted">
            {item.teacher_name} - {item.class_arm}
          </p>
        </div>
        <RiskBadge risk={item.risk_level} />
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="font-semibold text-ink">
            {formatPercentage(item.submission_rate)}
          </p>
          <p className="text-muted">submission rate</p>
        </div>
        <div>
          <p className="font-semibold text-ink">{item.not_started_count}</p>
          <p className="text-muted">not started</p>
        </div>
        <div>
          <p className="font-semibold text-ink">
            {item.submitted_count}/{item.expected_students}
          </p>
          <p className="text-muted">submitted</p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-muted">
        {item.recommended_action}
      </p>
      <div className="mt-4">
        <ActionLink action={item.action_payload} />
      </div>
    </div>
  );
}

function Section({
  title,
  description,
  children,
  emptyTitle,
  emptyDescription
}: {
  title: string;
  description: string;
  children: ReactNode;
  emptyTitle: string;
  emptyDescription: string;
}) {
  const hasChildren =
    Array.isArray(children) ? children.some(Boolean) : Boolean(children);

  return (
    <Card>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
      {hasChildren ? (
        <div className="mt-5 grid gap-4 xl:grid-cols-2">{children}</div>
      ) : (
        <div className="mt-4">
          <EmptyState title={emptyTitle} description={emptyDescription} />
        </div>
      )}
    </Card>
  );
}

export default function AdminInterventionsPage() {
  const [dashboard, setDashboard] =
    useState<AdminInterventionDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setDashboard(await getAdminInterventionDashboard());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load intervention dashboard."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const hasAnyIntervention = useMemo(() => {
    if (!dashboard) {
      return false;
    }
    return (
      dashboard.urgent_interventions.length > 0 ||
      dashboard.class_interventions.length > 0 ||
      dashboard.subject_interventions.length > 0 ||
      dashboard.teacher_interventions.length > 0 ||
      dashboard.weak_student_clusters.length > 0 ||
      dashboard.assignment_compliance_alerts.length > 0
    );
  }, [dashboard]);

  if (isLoading) {
    return <LoadingState label="Loading school interventions..." />;
  }

  if (error) {
    return <EmptyState title="Interventions unavailable" description={error} />;
  }

  if (!dashboard) {
    return (
      <EmptyState
        title="No intervention dashboard"
        description="Intervention data will appear after assignments and submissions exist."
      />
    );
  }

  return (
    <div data-testid="admin-intervention-dashboard">
      <PageHeader
        title="Interventions"
        description="Prioritize classes, subjects, teachers, and student groups that need academic support."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/analytics/weak-students">
              <Button variant="secondary">View Weak Students</Button>
            </Link>
            <Link href="/admin/analytics/compliance">
              <Button variant="secondary">View Compliance</Button>
            </Link>
          </div>
        }
      />

      <Card data-testid="admin-intervention-summary">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge risk={dashboard.overall_risk_level} />
              <Badge tone="brand">Risk score {dashboard.risk_score}/100</Badge>
            </div>
            <h2 className="mt-3 text-xl font-semibold text-ink">
              {dashboard.summary.message}
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Recommendations are computed from assignments, submissions,
              enrollments, teacher assignments, and approved question-bank
              availability. No AI is used.
            </p>
          </div>
          {dashboard.recommended_actions[0] ? (
            <ActionLink action={dashboard.recommended_actions[0].action_payload} />
          ) : null}
        </div>
      </Card>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="School average"
          value={formatPercentage(dashboard.summary.average_school_percentage)}
        />
        <StatCard
          label="Urgent interventions"
          value={dashboard.summary.total_urgent_interventions}
        />
        <StatCard
          label="Classes at risk"
          value={dashboard.summary.total_classes_at_risk}
        />
        <StatCard
          label="Subjects at risk"
          value={dashboard.summary.total_subjects_at_risk}
        />
        <StatCard
          label="Teachers needing follow-up"
          value={dashboard.summary.total_teachers_at_risk}
        />
        <StatCard
          label="Weak student clusters"
          value={dashboard.summary.total_weak_student_clusters}
        />
        <StatCard
          label="Compliance alerts"
          value={dashboard.summary.total_compliance_alerts}
        />
        <StatCard
          label="Overall risk"
          value={riskLabel(dashboard.summary.overall_risk_level)}
        />
      </section>

      {!hasAnyIntervention ? (
        <div className="mt-6">
          <EmptyState
            title="No intervention signals yet"
            description="This dashboard will surface risk once assignments are submitted and graded."
          />
        </div>
      ) : null}

      <section className="mt-6 space-y-6">
        <Section
          title="Urgent Interventions"
          description="The highest-priority actions across classes, subjects, teachers, weak clusters, and compliance."
          emptyTitle="No urgent interventions"
          emptyDescription="No urgent issues are currently detected."
        >
          {dashboard.urgent_interventions.map((item) => (
            <UrgentCard key={`${item.category}-${item.title}`} item={item} />
          ))}
        </Section>

        <Section
          title="Class Interventions"
          description="Classes with low performance, weak students, or submission risk."
          emptyTitle="No class interventions"
          emptyDescription="Class performance does not currently require intervention."
        >
          {dashboard.class_interventions.map((item) => (
            <ClassCard key={item.class_arm_id} item={item} />
          ))}
        </Section>

        <Section
          title="Subject Interventions"
          description="Subjects with weak class clusters, weak topics, or low average scores."
          emptyTitle="No subject interventions"
          emptyDescription="Subject performance is stable based on current submissions."
        >
          {dashboard.subject_interventions.map((item) => (
            <SubjectCard key={item.subject_id} item={item} />
          ))}
        </Section>

        <Section
          title="Teacher Interventions"
          description="Teacher activity, assignment creation, and class outcome signals that need follow-up."
          emptyTitle="No teacher interventions"
          emptyDescription="Teacher activity and class outcomes are currently stable."
        >
          {dashboard.teacher_interventions.map((item) => (
            <TeacherCard key={item.teacher_id} item={item} />
          ))}
        </Section>

        <Section
          title="Weak Student Clusters"
          description="Groups of students struggling with the same class, subject, and topic combination."
          emptyTitle="No weak clusters"
          emptyDescription="Weak student clusters will appear after graded submissions reveal topic gaps."
        >
          {dashboard.weak_student_clusters.map((item) => (
            <WeakClusterCard
              key={`${item.class_arm}-${item.subject}-${item.topic}`}
              item={item}
            />
          ))}
        </Section>

        <Section
          title="Assignment Compliance Alerts"
          description="Published assignments with low submission rates or many students who have not started."
          emptyTitle="No compliance alerts"
          emptyDescription="Assignment completion is healthy based on current published work."
        >
          {dashboard.assignment_compliance_alerts.map((item) => (
            <ComplianceCard key={item.assignment_id} item={item} />
          ))}
        </Section>

        <InterventionManagementPage baseRole="admin" />
      </section>
    </div>
  );
}
