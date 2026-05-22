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

const analyticsLinks = [
  {
    title: "Analytics Overview",
    href: "/admin/analytics",
    description: "Whole-school performance and risk summary."
  },
  {
    title: "Class Performance",
    href: "/admin/analytics/classes",
    description: "Compare class outcomes and submission rates."
  },
  {
    title: "Subject Performance",
    href: "/admin/analytics/subjects",
    description: "Review subject averages and weakest topics."
  },
  {
    title: "Teacher Activity",
    href: "/admin/analytics/teachers",
    description: "Monitor assignment activity by teacher."
  },
  {
    title: "Weak Students",
    href: "/admin/analytics/weak-students",
    description: "Find learners needing intervention."
  },
  {
    title: "Assignment Compliance",
    href: "/admin/analytics/compliance",
    description: "Track completion and not-started counts."
  }
];

export default function AdminDashboardPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadOverview() {
      try {
        setOverview(await getAdminOverview());
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

    void loadOverview();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading school analytics..." />;
  }

  if (error) {
    return <EmptyState title="Dashboard unavailable" description={error} />;
  }

  if (!overview) {
    return (
      <EmptyState
        title="No dashboard data"
        description="School analytics will appear once assignments and submissions exist."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="School dashboard"
        description="A whole-school view of enrollment, assignments, performance, and intervention signals."
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

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {analyticsLinks.map((link) => (
          <Card key={link.href}>
            <h2 className="text-base font-semibold text-ink">{link.title}</h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-muted">
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
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Recent Assignments
            </h2>
            <Link href="/admin/analytics/compliance">
              <Button variant="ghost">View Compliance</Button>
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {overview.recent_assignments.length ? (
              overview.recent_assignments.slice(0, 5).map((assignment) => (
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
              <p className="text-sm text-muted">No assignments yet.</p>
            )}
          </div>
        </Card>

        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold text-ink">
              Recent Low-Performing Students
            </h2>
            <Link href="/admin/analytics/weak-students">
              <Button variant="ghost">View Weak Students</Button>
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {overview.recent_low_performing_students.length ? (
              overview.recent_low_performing_students.slice(0, 5).map((student) => (
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
