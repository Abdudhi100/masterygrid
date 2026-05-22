"use client";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import {
  createAcademicSession,
  getAcademicSessions,
  updateAcademicSession
} from "@/lib/academics";
import { booleanValue, stringValue } from "@/lib/formPayload";
import type { AcademicSession } from "@/types/academics";

const initialValues: FormState = {
  name: "",
  starts_at: "",
  ends_at: "",
  is_active: false
};

export default function AcademicSessionsPage() {
  return (
    <ResourcePage<AcademicSession>
      title="Academic Sessions"
      description="Create and manage school years such as 2026/2027."
      createLabel="New session"
      load={getAcademicSessions}
      create={(payload) => createAcademicSession(payload)}
      update={(id, payload) => updateAcademicSession(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        name: row.name,
        starts_at: row.starts_at,
        ends_at: row.ends_at,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        name: stringValue(values.name),
        starts_at: stringValue(values.starts_at),
        ends_at: stringValue(values.ends_at),
        is_active: booleanValue(values.is_active)
      })}
      fields={[
        { name: "name", label: "Name", type: "text", required: true },
        { name: "starts_at", label: "Starts at", type: "date", required: true },
        { name: "ends_at", label: "Ends at", type: "date", required: true },
        { name: "is_active", label: "Active session", type: "checkbox" }
      ]}
      columns={[
        { key: "name", header: "Name", render: (row) => row.name },
        { key: "starts_at", header: "Starts", render: (row) => row.starts_at },
        { key: "ends_at", header: "Ends", render: (row) => row.ends_at },
        {
          key: "is_active",
          header: "Status",
          render: (row) => <BooleanBadge value={row.is_active} />
        }
      ]}
    />
  );
}
