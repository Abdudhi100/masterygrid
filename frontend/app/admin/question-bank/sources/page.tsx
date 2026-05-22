"use client";

import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState, ResourceField } from "@/components/admin/ResourceForm";
import type { ResourceColumn } from "@/components/admin/ResourceTable";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/hooks/useAuth";
import {
  createQuestionSource,
  getQuestionSources,
  updateQuestionSource
} from "@/lib/questionBank";
import type {
  QuestionSource,
  QuestionSourcePayload,
  QuestionSourceType
} from "@/types/questionBank";

const sourceTypeOptions: Array<{ value: QuestionSourceType; label: string }> = [
  { value: "jamb_past_question", label: "JAMB past question" },
  { value: "waec_past_question", label: "WAEC past question" },
  { value: "neco_past_question", label: "NECO past question" },
  { value: "teacher_created", label: "Teacher created" },
  { value: "ai_generated", label: "AI generated" },
  { value: "school_created", label: "School created" }
];

const initialValues: FormState = {
  name: "",
  source_type: "school_created",
  exam_body: "",
  year: "",
  description: "",
  is_active: true
};

const fields: ResourceField[] = [
  { name: "name", label: "Name", type: "text", required: true },
  {
    name: "source_type",
    label: "Source type",
    type: "select",
    required: true,
    options: sourceTypeOptions
  },
  { name: "exam_body", label: "Exam body", type: "text" },
  { name: "year", label: "Year", type: "text" },
  { name: "description", label: "Description", type: "textarea" },
  { name: "is_active", label: "Active", type: "checkbox" }
];

const columns: ResourceColumn<QuestionSource>[] = [
  {
    key: "name",
    header: "Name",
    render: (row) => row.name
  },
  {
    key: "source_type",
    header: "Type",
    render: (row) => row.source_type.replaceAll("_", " ")
  },
  {
    key: "exam_body",
    header: "Exam body",
    render: (row) => row.exam_body || "Not set"
  },
  {
    key: "year",
    header: "Year",
    render: (row) => row.year ?? "Not set"
  },
  {
    key: "is_active",
    header: "Status",
    render: (row) => (
      <Badge tone={row.is_active ? "success" : "neutral"}>
        {row.is_active ? "active" : "inactive"}
      </Badge>
    )
  }
];

function toFormValues(source: QuestionSource): FormState {
  return {
    name: source.name,
    source_type: source.source_type,
    exam_body: source.exam_body,
    year: source.year ? String(source.year) : "",
    description: source.description,
    is_active: source.is_active
  };
}

function toPayload(values: FormState): QuestionSourcePayload {
  const year = String(values.year ?? "").trim();
  return {
    name: String(values.name ?? "").trim(),
    source_type: values.source_type as QuestionSourceType,
    exam_body: String(values.exam_body ?? "").trim(),
    year: year ? Number(year) : null,
    description: String(values.description ?? "").trim(),
    is_active: Boolean(values.is_active)
  };
}

export default function AdminQuestionSourcesPage() {
  const { user } = useAuth();
  const canManageSources = Boolean(
    user && (user.role === "platform_admin" || user.is_superuser)
  );

  return (
    <ResourcePage<QuestionSource>
      title="Question Sources"
      description="Manage source metadata used to label question bank items."
      createLabel="Create Source"
      columns={columns}
      fields={fields}
      load={() => getQuestionSources()}
      create={(payload) => createQuestionSource(payload as QuestionSourcePayload)}
      update={(id, payload) =>
        updateQuestionSource(id, payload as Partial<QuestionSourcePayload>)
      }
      initialValues={initialValues}
      toFormValues={toFormValues}
      toPayload={toPayload}
      canCreate={canManageSources}
      canEdit={canManageSources}
      unavailableMessage={
        canManageSources
          ? undefined
          : "Source creation and editing are available to platform admins only."
      }
    />
  );
}
