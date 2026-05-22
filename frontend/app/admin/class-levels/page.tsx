"use client";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { createClassLevel, getClassLevels, updateClassLevel } from "@/lib/academics";
import { booleanValue, stringValue } from "@/lib/formPayload";
import type { ClassLevel } from "@/types/academics";

const initialValues: FormState = {
  name: "",
  description: "",
  is_active: true
};

export default function ClassLevelsPage() {
  return (
    <ResourcePage<ClassLevel>
      title="Class Levels"
      description="Manage SS1, SS2, SS3 and any school-specific class levels."
      createLabel="New class level"
      load={getClassLevels}
      create={(payload) => createClassLevel(payload)}
      update={(id, payload) => updateClassLevel(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        name: row.name,
        description: row.description,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        name: stringValue(values.name),
        description: stringValue(values.description),
        is_active: booleanValue(values.is_active)
      })}
      fields={[
        { name: "name", label: "Name", type: "text", required: true },
        { name: "description", label: "Description", type: "textarea" },
        { name: "is_active", label: "Active class level", type: "checkbox" }
      ]}
      columns={[
        { key: "name", header: "Name", render: (row) => row.name },
        {
          key: "description",
          header: "Description",
          render: (row) => row.description || "Not set"
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
