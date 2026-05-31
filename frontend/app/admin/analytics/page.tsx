"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { getAdminOverview } from "@/lib/analytics";
import { ApiError } from "@/lib/api";
import type { AdminOverview } from "@/types/analytics";
import {
  formatDate,
  formatPercentage,
  ScoreBadge,
  StatusBadge
} from "@/app/admin/analytics/_components/analyticsUi";

const quickLinks = [
  {
    title: "Interventions",
    href: "/admin/interventions",
    description: "Prioritize classes, subjects, teachers, and groups needing support."
  },
  {
    title: "Class Performance",
    href: "/admin/analytics/classes",
    description: "Compare performance and submission coverage by class."
  },
  {
    title: "Subject Performance",
    href: "/admin/analytics/subjects",
    description: "Find weak subjects and topics across the school."
  },
  {
    title: "Teacher Activity",
    href: "/admin/analytics/teachers",
    description: "Monitor teacher assignment creation and class outcomes."
  },
  {
    title: "Weak Students",
    href: "/admin/analytics/weak-students",
    description: "Review learners who need school-wide intervention."
  },
  {
    title: "Assignment Compliance",
    href: "/admin/analytics/compliance",
    description: "Track completion rates and not-started assignments."
  }
];

export default function AdminAnalyticsOverviewPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadOverview() {
      try {
        setOverview(await getAdminOverview());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load school analytics."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadOverview();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading school analytics..." />;
  }

  if (error) {
    return <EmptyState title="Analytics unavailable" description={error} />;
  }

  if (!overview) {
    return (
      <EmptyState
        title="No analytics data"
        description="School analytics will appear once assignments and submissions exist."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="School Analytics"
        description="Monitor whole-school academic performance, completion, and support needs."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <StatCard label="Students" value={overview.total_students} />
        <StatCard label="Teachers" value={overview.total_teachers} />
        <StatCard label="Class arms" value={overview.total_class_arms} />
        <StatCard label="Subjects" value={overview.total_subjects} />
        <StatCard label="Assignments" value={overview.total_assignments} />
        <StatCard label="Published" value={overview.published_assignments} />
        <StatCard label="Graded submissions" value={overview.graded_submissions} />
        <StatCard
          label="School average"
          value={formatPercentage(overview.average_school_percentage)}
        />
        <StatCard label="Weak students" value={overview.weak_students_count} />
        <StatCard label="Weak classes" value={overview.weak_classes_count} />
        <StatCard label="Weak subjects" value={overview.weak_subjects_count} />
        <StatCard
          label="Pending or not started"
          value={overview.pending_or_not_started_submissions}
        />
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {quickLinks.map((link) => (
          <Card key={link.href}>
            <h2 className="text-base font-semibold text-ink">{link.title}</h2>
            <p className="mt-2 min-h-16 text-sm leading-6 text-muted">
              {link.description}
            </p>
            <Link href={link.href} className="mt-4 inline-block">
              <Button variant="secondary">Open</Button>
            </Link>
          </Card>
        ))}
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink">Recent Assignments</h2>
          <div className="mt-4 space-y-3">
            {overview.recent_assignments.length ? (
              overview.recent_assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-semibold text-ink">{assignment.title}</p>
                      <p className="mt-1 text-sm text-muted">
                        {assignment.teacher_name} - {assignment.class_arm}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        {assignment.subject} - {assignment.topic} - Due{" "}
                        {formatDate(assignment.due_at)}
                      </p>
                    </div>
                    <StatusBadge value={assignment.status} />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No recent assignments yet.</p>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-ink">
            Recent Low-Performing Students
          </h2>
          <div className="mt-4 space-y-3">
            {overview.recent_low_performing_students.length ? (
              overview.recent_low_performing_students.map((student) => (
                <div
                  key={`${student.student_id}-${student.assignment_id}`}
                  className="rounded-md border border-line bg-surface p-3"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-semibold text-ink">
                        {student.student_name}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        {student.class_arm ?? "Class not set"} -{" "}
                        {student.assignment_title}
                      </p>
                      <p className="mt-1 text-sm text-muted">
                        Graded {formatDate(student.graded_at)}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-ink">
                        {formatPercentage(student.percentage)}
                      </span>
                      <ScoreBadge percentage={student.percentage} />
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No low-performance alerts yet.</p>
            )}
          </div>
        </Card>
      </section>
    </>
  );
}
