"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  InterventionCategoryBadge,
  InterventionPriorityBadge,
  InterventionStatusBadge,
  titleCase
} from "@/components/interventions/InterventionBadges";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import {
  addInterventionNote,
  getIntervention,
  updateIntervention
} from "@/lib/interventions";
import type {
  InterventionPriority,
  InterventionStatus,
  StudentIntervention
} from "@/types/interventions";

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

export function InterventionDetailPage({
  interventionId,
  baseRole
}: {
  interventionId: string;
  baseRole: "admin" | "teacher";
}) {
  const [intervention, setIntervention] = useState<StudentIntervention | null>(
    null
  );
  const [status, setStatus] = useState<InterventionStatus>("open");
  const [priority, setPriority] = useState<InterventionPriority>("medium");
  const [dueDate, setDueDate] = useState("");
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadIntervention = useCallback(async () => {
    try {
      const data = await getIntervention(interventionId);
      setIntervention(data);
      setStatus(data.status);
      setPriority(data.priority);
      setDueDate(data.due_date ?? "");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load intervention."
      );
    } finally {
      setIsLoading(false);
    }
  }, [interventionId]);

  useEffect(() => {
    void loadIntervention();
  }, [loadIntervention]);

  async function handleSaveStatus() {
    setIsSaving(true);
    setError("");
    setMessage("");
    try {
      const updated = await updateIntervention(interventionId, {
        status,
        priority,
        due_date: dueDate || null
      });
      setIntervention(updated);
      setMessage("Intervention updated.");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to update intervention."
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAddNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!note.trim()) {
      return;
    }

    setIsAddingNote(true);
    setError("");
    setMessage("");
    try {
      await addInterventionNote(interventionId, { note });
      setNote("");
      await loadIntervention();
      setMessage("Note added.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to add note.");
    } finally {
      setIsAddingNote(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading intervention..." />;
  }

  if (error && !intervention) {
    return <EmptyState title="Intervention unavailable" description={error} />;
  }

  if (!intervention) {
    return (
      <EmptyState
        title="No intervention found"
        description="This intervention could not be loaded."
      />
    );
  }

  return (
    <div data-testid="intervention-detail-page">
      <PageHeader
        title={intervention.title}
        description="Track intervention status, ownership, follow-up notes, and outcome."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href={`/${baseRole}/students/${intervention.student}/interventions`}>
              <Button variant="secondary">Student Interventions</Button>
            </Link>
            <Link href={`/${baseRole}/interventions`}>
              <Button variant="secondary">All Interventions</Button>
            </Link>
          </div>
        }
      />

      {error ? (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}
      {message ? (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-6">
          <Card>
            <div className="flex flex-wrap items-center gap-2">
              <InterventionStatusBadge status={intervention.status} />
              <InterventionPriorityBadge priority={intervention.priority} />
              <InterventionCategoryBadge category={intervention.category} />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-ink">
              {intervention.student_name}
            </h2>
            <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-semibold text-ink">Student email</dt>
                <dd className="mt-1 text-muted">{intervention.student_email}</dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Class arm</dt>
                <dd className="mt-1 text-muted">
                  {intervention.student_class_arm || "Not set"}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Created by</dt>
                <dd className="mt-1 text-muted">
                  {intervention.created_by_name || "Not set"}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Assigned to</dt>
                <dd className="mt-1 text-muted">
                  {intervention.assigned_to_name || "Unassigned"}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Due date</dt>
                <dd className="mt-1 text-muted">
                  {intervention.due_date ?? "Not set"}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-ink">Completed</dt>
                <dd className="mt-1 text-muted">
                  {formatDate(intervention.completed_at)}
                </dd>
              </div>
            </dl>
            <div className="mt-5 rounded-md border border-line bg-surface p-4">
              <p className="text-sm font-semibold text-ink">Description</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted">
                {intervention.description || "No description provided."}
              </p>
            </div>
            <div className="mt-5 text-sm text-muted">
              Source: {titleCase(intervention.source_type)}
              {intervention.source_topic_title
                ? ` - ${intervention.source_topic_title}`
                : ""}
            </div>
          </Card>

          <Card>
            <h2 className="text-base font-semibold text-ink">Notes Timeline</h2>
            <form onSubmit={handleAddNote} className="mt-4 space-y-3">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-ink">
                  Add note
                </span>
                <textarea
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  rows={4}
                  className="w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
                  data-testid="intervention-note-input"
                />
              </label>
              <Button
                type="submit"
                isLoading={isAddingNote}
                disabled={!note.trim()}
                data-testid="intervention-add-note-button"
              >
                Add Note
              </Button>
            </form>

            <div className="mt-6 space-y-3">
              {intervention.notes?.length ? (
                intervention.notes.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-md border border-line bg-surface p-4"
                    data-testid="intervention-note-card"
                  >
                    <p className="whitespace-pre-wrap text-sm leading-6 text-ink">
                      {item.note}
                    </p>
                    <p className="mt-3 text-xs font-semibold text-muted">
                      {item.author_name || "Unknown"} - {formatDate(item.created_at)}
                    </p>
                  </div>
                ))
              ) : (
                <EmptyState
                  title="No notes yet"
                  description="Add a note whenever a follow-up action happens."
                />
              )}
            </div>
          </Card>
        </div>

        <Card>
          <h2 className="text-base font-semibold text-ink">Update Tracking</h2>
          <div className="mt-4 space-y-4">
            <Select
              label="Status"
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as InterventionStatus)
              }
              options={[
                { value: "open", label: "Open" },
                { value: "in_progress", label: "In Progress" },
                { value: "resolved", label: "Resolved" },
                { value: "closed", label: "Closed" }
              ]}
              data-testid="intervention-status-select"
            />
            <Select
              label="Priority"
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as InterventionPriority)
              }
              options={[
                { value: "low", label: "Low" },
                { value: "medium", label: "Medium" },
                { value: "high", label: "High" },
                { value: "urgent", label: "Urgent" }
              ]}
            />
            <Input
              label="Due date"
              type="date"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
            <Button
              type="button"
              onClick={handleSaveStatus}
              isLoading={isSaving}
              data-testid="intervention-save-status-button"
            >
              Save Status
            </Button>
          </div>
        </Card>
      </section>
    </div>
  );
}
