"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import {
  createIntervention,
  createInterventionFromProgressReport
} from "@/lib/interventions";
import type {
  InterventionCategory,
  InterventionPriority,
  InterventionSourceType,
  StudentIntervention
} from "@/types/interventions";

const categories: Array<{ value: InterventionCategory; label: string }> = [
  { value: "academic_support", label: "Academic Support" },
  { value: "parent_contact", label: "Parent Contact" },
  { value: "remedial_assignment", label: "Remedial Assignment" },
  { value: "revision_class", label: "Revision Class" },
  { value: "attendance_followup", label: "Attendance Follow-up" },
  { value: "behavior_followup", label: "Behavior Follow-up" },
  { value: "other", label: "Other" }
];

const priorities: Array<{ value: InterventionPriority; label: string }> = [
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
  { value: "low", label: "Low" }
];

type InterventionFormProps = {
  studentId: number | string;
  sourceType?: InterventionSourceType;
  defaultTitle?: string;
  defaultDescription?: string;
  defaultPriority?: InterventionPriority;
  onCreated: (intervention: StudentIntervention) => void;
};

export function InterventionForm({
  studentId,
  sourceType = "manual",
  defaultTitle = "",
  defaultDescription = "",
  defaultPriority = "medium",
  onCreated
}: InterventionFormProps) {
  const [title, setTitle] = useState(defaultTitle);
  const [description, setDescription] = useState(defaultDescription);
  const [category, setCategory] =
    useState<InterventionCategory>("academic_support");
  const [priority, setPriority] = useState<InterventionPriority>(defaultPriority);
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const payload = {
        student: Number(studentId),
        title,
        description,
        category,
        priority,
        due_date: dueDate || null
      };
      const intervention =
        sourceType === "progress_report"
          ? await createInterventionFromProgressReport(payload)
          : await createIntervention({ ...payload, source_type: sourceType });
      setTitle("");
      setDescription("");
      setDueDate("");
      onCreated(intervention);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to create intervention."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4"
      data-testid="intervention-form"
    >
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Input
        label="Title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        required
        data-testid="intervention-title-input"
      />

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">
          Description
        </span>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={5}
          className="w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
          data-testid="intervention-description-input"
        />
      </label>

      <div className="grid gap-4 md:grid-cols-3">
        <Select
          label="Category"
          value={category}
          onChange={(event) =>
            setCategory(event.target.value as InterventionCategory)
          }
          options={categories}
          data-testid="intervention-category-select"
        />
        <Select
          label="Priority"
          value={priority}
          onChange={(event) =>
            setPriority(event.target.value as InterventionPriority)
          }
          options={priorities}
          data-testid="intervention-priority-select"
        />
        <Input
          label="Due date"
          type="date"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
        />
      </div>

      <Button
        type="submit"
        isLoading={isSubmitting}
        disabled={!title.trim()}
        data-testid="intervention-submit-button"
      >
        Create Intervention
      </Button>
    </form>
  );
}
