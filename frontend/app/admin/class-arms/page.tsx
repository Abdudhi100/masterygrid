"use client";

import { useEffect, useMemo, useState } from "react";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  createClassArm,
  getClassArms,
  getClassLevels,
  updateClassArm
} from "@/lib/academics";
import { booleanValue, numberValue, stringValue } from "@/lib/formPayload";
import type { ClassArm, ClassLevel } from "@/types/academics";

const initialValues: FormState = {
  class_level: "",
  name: "",
  description: "",
  is_active: true
};

export default function ClassArmsPage() {
  const [classLevels, setClassLevels] = useState<ClassLevel[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      setClassLevels(await getClassLevels());
      setIsLoadingOptions(false);
    }
    void loadOptions();
  }, []);

  const fields = useMemo(
    () => [
      {
        name: "class_level",
        label: "Class level",
        type: "select" as const,
        required: true,
        options: classLevels.map((level) => ({
          value: String(level.id),
          label: level.name
        }))
      },
      { name: "name", label: "Arm name", type: "text" as const, required: true },
      { name: "description", label: "Description", type: "textarea" as const },
      { name: "is_active", label: "Active class arm", type: "checkbox" as const }
    ],
    [classLevels]
  );

  if (isLoadingOptions) {
    return <LoadingState label="Loading class levels..." />;
  }

  return (
    <ResourcePage<ClassArm>
      title="Class Arms"
      description="Manage class arms and streams such as SS1 Science A."
      createLabel="New class arm"
      load={getClassArms}
      create={(payload) => createClassArm(payload)}
      update={(id, payload) => updateClassArm(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        class_level: String(row.class_level),
        name: row.name,
        description: row.description,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        class_level: numberValue(values.class_level),
        name: stringValue(values.name),
        description: stringValue(values.description),
        is_active: booleanValue(values.is_active)
      })}
      fields={fields}
      columns={[
        {
          key: "display_name",
          header: "Class arm",
          render: (row) => row.display_name ?? row.name
        },
        {
          key: "class_level",
          header: "Level",
          render: (row) => row.class_level_name ?? row.class_level
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
