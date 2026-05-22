"use client";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { createSubject, getSubjects, updateSubject } from "@/lib/academics";
import { booleanValue, stringValue } from "@/lib/formPayload";
import type { Subject } from "@/types/academics";

const initialValues: FormState = {
  name: "",
  code: "",
  description: "",
  is_jamb_subject: true,
  is_active: true
};

export default function SubjectsPage() {
  return (
    <ResourcePage<Subject>
      title="Subjects"
      description="Manage subjects used for topics, question banks, and assignments."
      createLabel="New subject"
      load={getSubjects}
      create={(payload) => createSubject(payload)}
      update={(id, payload) => updateSubject(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        name: row.name,
        code: row.code,
        description: row.description,
        is_jamb_subject: row.is_jamb_subject,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        name: stringValue(values.name),
        code: stringValue(values.code),
        description: stringValue(values.description),
        is_jamb_subject: booleanValue(values.is_jamb_subject),
        is_active: booleanValue(values.is_active)
      })}
      fields={[
        { name: "name", label: "Name", type: "text", required: true },
        { name: "code", label: "Code", type: "text" },
        { name: "description", label: "Description", type: "textarea" },
        { name: "is_jamb_subject", label: "JAMB subject", type: "checkbox" },
        { name: "is_active", label: "Active subject", type: "checkbox" }
      ]}
      columns={[
        { key: "name", header: "Name", render: (row) => row.name },
        { key: "code", header: "Code", render: (row) => row.code || "Not set" },
        { key: "scope", header: "Scope", render: (row) => row.scope ?? "school" },
        {
          key: "is_jamb_subject",
          header: "JAMB",
          render: (row) => (
            <BooleanBadge value={row.is_jamb_subject} trueLabel="Yes" falseLabel="No" />
          )
        },
        {
          key: "is_active",
          header: "Status",
          render: (row) => <BooleanBadge value={row.is_active} />
        }
      ]}
    />
  );
}
