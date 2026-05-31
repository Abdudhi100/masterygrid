"use client";

import Link from "next/link";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { Button } from "@/components/ui/Button";
import { getStudents, registerStudent } from "@/lib/academics";
import { stringValue } from "@/lib/formPayload";
import { useAuth } from "@/hooks/useAuth";
import type { Student, StudentRegistrationPayload } from "@/types/academics";

const initialValues: FormState = {
  full_name: "",
  email: "",
  password: "",
  admission_number: "",
  guardian_name: "",
  guardian_phone: ""
};

export default function StudentsPage() {
  const { user } = useAuth();

  return (
    <ResourcePage<Student>
      title="Students"
      description="Create and manage student accounts before enrolling them into class arms."
      createLabel="New student"
      load={getStudents}
      create={async (payload) => {
        await registerStudent(payload as StudentRegistrationPayload);
        return {} as Student;
      }}
      canEdit={false}
      initialValues={initialValues}
      toPayload={(values) => ({
        full_name: stringValue(values.full_name),
        email: stringValue(values.email),
        password: stringValue(values.password),
        role: "student",
        school: user?.school ?? null,
        admission_number: stringValue(values.admission_number),
        guardian_name: stringValue(values.guardian_name),
        guardian_phone: stringValue(values.guardian_phone)
      })}
      fields={[
        { name: "full_name", label: "Full name", type: "text", required: true },
        { name: "email", label: "Email address", type: "email", required: true },
        { name: "password", label: "Password", type: "password", required: true },
        {
          name: "admission_number",
          label: "Admission number",
          type: "text",
          required: true
        },
        { name: "guardian_name", label: "Guardian name", type: "text" },
        { name: "guardian_phone", label: "Guardian phone", type: "text" }
      ]}
      columns={[
        { key: "full_name", header: "Name", render: (row) => row.full_name },
        { key: "email", header: "Email", render: (row) => row.email },
        {
          key: "admission_number",
          header: "Admission no.",
          render: (row) => row.student_profile?.admission_number || "Not set"
        },
        {
          key: "guardian_name",
          header: "Guardian",
          render: (row) => row.student_profile?.guardian_name || "Not set"
        },
        {
          key: "guardian_phone",
          header: "Guardian phone",
          render: (row) => row.student_profile?.guardian_phone || "Not set"
        },
        {
          key: "is_active",
          header: "Status",
          render: (row) => <BooleanBadge value={row.is_active} />
        },
        {
          key: "progress_report",
          header: "Progress",
          render: (row) => (
            <Link
              href={`/admin/students/${row.id}/progress-report`}
              data-testid="student-progress-link"
            >
              <Button variant="secondary">Progress Report</Button>
            </Link>
          )
        }
      ]}
    />
  );
}
