"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { InterventionForm } from "@/components/interventions/InterventionForm";
import { InterventionList } from "@/components/interventions/InterventionList";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getStudentProgressReport } from "@/lib/analytics";
import { getStudentInterventions } from "@/lib/interventions";
import type { StudentProgressReport } from "@/types/analytics";
import type { StudentIntervention } from "@/types/interventions";

export function StudentInterventionsPage({
  studentId,
  baseRole
}: {
  studentId: string;
  baseRole: "admin" | "teacher";
}) {
  const searchParams = useSearchParams();
  const [report, setReport] = useState<StudentProgressReport | null>(null);
  const [interventions, setInterventions] = useState<StudentIntervention[]>([]);
  const [showForm, setShowForm] = useState(searchParams.get("create") === "1");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [progressReport, studentInterventions] = await Promise.all([
        getStudentProgressReport(studentId),
        getStudentInterventions(studentId)
      ]);
      setReport(progressReport);
      setInterventions(studentInterventions);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load student interventions."
      );
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  if (isLoading) {
    return <LoadingState label="Loading student interventions..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Interventions unavailable"
        description={error}
        dashboardHref={`/${baseRole}/dashboard`}
      />
    );
  }

  return (
    <div data-testid="student-interventions-page">
      <PageHeader
        title={`${report?.student.full_name ?? "Student"} Interventions`}
        description="Record follow-up actions, parent contact, remedial work, and progress notes for this student."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={() => setShowForm((current) => !current)}
              data-testid="intervention-create-button"
            >
              {showForm ? "Hide Form" : "Create Intervention"}
            </Button>
            <Link href={`/${baseRole}/students/${studentId}/progress-report`}>
              <Button variant="secondary">Progress Report</Button>
            </Link>
          </div>
        }
      />

      {report ? (
        <Card>
          <div className="grid gap-4 text-sm md:grid-cols-4">
            <div>
              <p className="font-semibold text-ink">Email</p>
              <p className="mt-1 break-words text-muted">{report.student.email}</p>
            </div>
            <div>
              <p className="font-semibold text-ink">Admission number</p>
              <p className="mt-1 text-muted">
                {report.student.admission_number ?? "Not set"}
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Class arm</p>
              <p className="mt-1 text-muted">
                {report.student.class_arm ?? "Not set"}
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Risk level</p>
              <p className="mt-1 text-muted">{report.summary.risk_level}</p>
            </div>
          </div>
        </Card>
      ) : null}

      {showForm ? (
        <Card className="mt-6">
          <h2 className="text-base font-semibold text-ink">Create Intervention</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Use this record to track the next support action and follow-up notes.
          </p>
          <div className="mt-5">
            <InterventionForm
              studentId={studentId}
              sourceType="progress_report"
              defaultTitle="Progress report follow-up"
              defaultDescription="Follow up on the student's latest progress report."
              onCreated={(intervention) => {
                setInterventions((current) => [intervention, ...current]);
                setShowForm(false);
              }}
            />
          </div>
        </Card>
      ) : null}

      <section className="mt-6">
        <InterventionList
          interventions={interventions}
          baseRole={baseRole}
          emptyTitle="No interventions for this student"
          emptyDescription="Create the first intervention when a support action needs tracking."
        />
      </section>
    </div>
  );
}
