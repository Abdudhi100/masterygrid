"use client";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { getTeachers, registerTeacher } from "@/lib/academics";
import { stringValue } from "@/lib/formPayload";
import { useAuth } from "@/hooks/useAuth";
import type { Teacher, TeacherRegistrationPayload } from "@/types/academics";

const initialValues: FormState = {
  full_name: "",
  email: "",
  password: "",
  staff_id: "",
  phone_number: ""
};

export default function TeachersPage() {
  const { user } = useAuth();

  return (
    <ResourcePage<Teacher>
      title="Teachers"
      description="Create and manage teacher accounts for your school."
      createLabel="New teacher"
      load={getTeachers}
      create={async (payload) => {
        await registerTeacher(payload as TeacherRegistrationPayload);
        return {} as Teacher;
      }}
      canEdit={false}
      initialValues={initialValues}
      toPayload={(values) => ({
        full_name: stringValue(values.full_name),
        email: stringValue(values.email),
        password: stringValue(values.password),
        role: "teacher",
        school: user?.school ?? null,
        staff_id: stringValue(values.staff_id),
        phone_number: stringValue(values.phone_number)
      })}
      fields={[
        { name: "full_name", label: "Full name", type: "text", required: true },
        { name: "email", label: "Email address", type: "email", required: true },
        { name: "password", label: "Password", type: "password", required: true },
        { name: "staff_id", label: "Staff ID", type: "text", required: true },
        { name: "phone_number", label: "Phone number", type: "text" }
      ]}
      columns={[
        { key: "full_name", header: "Name", render: (row) => row.full_name },
        { key: "email", header: "Email", render: (row) => row.email },
        {
          key: "staff_id",
          header: "Staff ID",
          render: (row) => row.teacher_profile?.staff_id || "Not set"
        },
        {
          key: "phone_number",
          header: "Phone",
          render: (row) => row.teacher_profile?.phone_number || "Not set"
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
