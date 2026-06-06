"use client";

import { useCallback, useEffect, useState } from "react";

import { InterventionList } from "@/components/interventions/InterventionList";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import { getInterventions } from "@/lib/interventions";
import type {
  InterventionCategory,
  InterventionPriority,
  InterventionStatus,
  StudentIntervention
} from "@/types/interventions";

export function InterventionManagementPage({
  baseRole
}: {
  baseRole: "admin" | "teacher";
}) {
  const [interventions, setInterventions] = useState<StudentIntervention[]>([]);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadInterventions = useCallback(async () => {
    setIsLoading(true);
    try {
      setInterventions(
        await getInterventions({
          status,
          priority,
          category,
          search
        })
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load interventions."
      );
    } finally {
      setIsLoading(false);
    }
  }, [category, priority, search, status]);

  useEffect(() => {
    void loadInterventions();
  }, [loadInterventions]);

  if (error && !interventions.length) {
    return (
      <ErrorState
        title="Interventions unavailable"
        description={error}
        dashboardHref={`/${baseRole}/dashboard`}
      />
    );
  }

  return (
    <div data-testid="intervention-list-page">
      <PageHeader
        title="Intervention Tracking"
        description="Track student support actions, notes, ownership, due dates, and outcomes."
      />

      <Card>
        <div className="grid gap-4 md:grid-cols-4">
          <Input
            label="Search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Student, title, or detail"
          />
          <Select
            label="Status"
            value={status}
            onChange={(event) => setStatus(event.target.value as InterventionStatus | "")}
            options={[
              { value: "", label: "All statuses" },
              { value: "open", label: "Open" },
              { value: "in_progress", label: "In Progress" },
              { value: "resolved", label: "Resolved" },
              { value: "closed", label: "Closed" }
            ]}
          />
          <Select
            label="Priority"
            value={priority}
            onChange={(event) =>
              setPriority(event.target.value as InterventionPriority | "")
            }
            options={[
              { value: "", label: "All priorities" },
              { value: "urgent", label: "Urgent" },
              { value: "high", label: "High" },
              { value: "medium", label: "Medium" },
              { value: "low", label: "Low" }
            ]}
          />
          <Select
            label="Category"
            value={category}
            onChange={(event) =>
              setCategory(event.target.value as InterventionCategory | "")
            }
            options={[
              { value: "", label: "All categories" },
              { value: "academic_support", label: "Academic Support" },
              { value: "parent_contact", label: "Parent Contact" },
              { value: "remedial_assignment", label: "Remedial Assignment" },
              { value: "revision_class", label: "Revision Class" },
              { value: "attendance_followup", label: "Attendance Follow-up" },
              { value: "behavior_followup", label: "Behavior Follow-up" },
              { value: "other", label: "Other" }
            ]}
          />
        </div>
      </Card>

      <section className="mt-6">
        {isLoading ? (
          <LoadingState label="Loading interventions..." />
        ) : (
          <InterventionList interventions={interventions} baseRole={baseRole} />
        )}
      </section>
    </div>
  );
}
