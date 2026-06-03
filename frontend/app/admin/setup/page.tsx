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
import { getSchoolSetupStatus } from "@/lib/schools";
import type { SchoolSetupStatus, SchoolSetupStep } from "@/types/schools";

function statusTone(status: SchoolSetupStep["status"]) {
  if (status === "complete") {
    return "success";
  }
  if (status === "warning") {
    return "warning";
  }
  return "danger";
}

function statusLabel(status: SchoolSetupStep["status"]) {
  return status.replaceAll("_", " ");
}

function StepCard({ step, index }: { step: SchoolSetupStep; index: number }) {
  return (
    <Card data-testid="school-setup-step" className="h-full">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-muted">
              Step {index + 1}
            </span>
            <Badge
              data-testid="school-setup-step-status"
              tone={statusTone(step.status)}
            >
              {statusLabel(step.status)}
            </Badge>
          </div>
          <h2 className="mt-3 text-lg font-semibold text-ink">{step.label}</h2>
          <p className="mt-2 text-sm leading-6 text-muted">{step.description}</p>
          <p className="mt-3 text-sm leading-6 text-ink">
            {step.recommendation}
          </p>
        </div>
        <div className="shrink-0 text-left sm:text-right">
          <p className="text-sm font-semibold text-ink">
            {step.count} / {step.required_count}
          </p>
          <p className="mt-1 text-xs text-muted">required</p>
        </div>
      </div>
      <Link
        href={step.action_url}
        data-testid="school-setup-action-link"
        className="mt-4 inline-block"
      >
        <Button variant={step.status === "complete" ? "secondary" : "primary"}>
          {step.status === "complete" ? "Review" : "Set Up"}
        </Button>
      </Link>
    </Card>
  );
}

export default function AdminSetupWizardPage() {
  const [status, setStatus] = useState<SchoolSetupStatus | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadStatus() {
      try {
        setStatus(await getSchoolSetupStatus());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load school setup status."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadStatus();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading setup wizard..." />;
  }

  if (error) {
    return <EmptyState title="Setup wizard unavailable" description={error} />;
  }

  if (!status) {
    return (
      <EmptyState
        title="No setup status"
        description="School setup status could not be loaded."
      />
    );
  }

  const completeSteps = status.steps.filter((step) => step.status === "complete");
  const incompleteSteps = status.steps.filter(
    (step) => step.status !== "complete"
  );

  return (
    <div data-testid="school-setup-page">
      <PageHeader
        title="Setup Wizard"
        description={`Guide ${status.school_name} through the core setup needed for assignments, practice, analytics, and question-bank workflows.`}
        actions={
          <Link href="/admin/dashboard">
            <Button variant="secondary">Back to Dashboard</Button>
          </Link>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Completion"
          value={`${status.completion_percentage}%`}
          helper={
            status.is_setup_complete
              ? "All required setup steps are complete."
              : "Complete the remaining setup steps below."
          }
        />
        <StatCard label="Complete Steps" value={completeSteps.length} />
        <StatCard label="Remaining Steps" value={incompleteSteps.length} />
        <StatCard
          label="School"
          value={status.school_name}
          helper={`ID ${status.school_id}`}
        />
      </section>

      <Card className="mt-6" data-testid="school-setup-progress">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">
              Onboarding progress
            </h2>
            <p className="mt-1 text-sm text-muted">
              {completeSteps.length} of {status.steps.length} required steps are
              complete.
            </p>
          </div>
          <Badge tone={status.is_setup_complete ? "success" : "warning"}>
            {status.is_setup_complete ? "Complete" : "In progress"}
          </Badge>
        </div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600 transition-all"
            style={{ width: `${status.completion_percentage}%` }}
          />
        </div>
      </Card>

      {status.next_step ? (
        <Card
          className="mt-6 border-brand-100 bg-brand-50"
          data-testid="school-setup-next-step"
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold text-brand-700">
                Next recommended step
              </p>
              <h2 className="mt-2 text-xl font-semibold text-ink">
                {status.next_step.label}
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                {status.next_step.recommendation}
              </p>
            </div>
            <Link
              href={status.next_step.action_url}
              data-testid="school-setup-action-link"
            >
              <Button>Continue Setup</Button>
            </Link>
          </div>
        </Card>
      ) : (
        <Card
          className="mt-6 border-emerald-100 bg-emerald-50"
          data-testid="school-setup-next-step"
        >
          <h2 className="text-xl font-semibold text-ink">Setup complete</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            The core school setup is complete. You can still review or update any
            setup area from the checklist below.
          </p>
        </Card>
      )}

      {status.warnings.length ? (
        <Card className="mt-6 border-amber-100 bg-amber-50">
          <h2 className="text-base font-semibold text-ink">Warnings</h2>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
            {status.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        {status.steps.map((step, index) => (
          <StepCard key={step.key} step={step} index={index} />
        ))}
      </section>
    </div>
  );
}
