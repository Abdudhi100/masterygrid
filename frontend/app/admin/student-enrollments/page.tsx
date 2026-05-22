"use client";

import { useEffect, useMemo, useState } from "react";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  createStudentEnrollment,
  getAcademicSessions,
  getClassArms,
  getStudentEnrollments,
  getStudents,
  getTerms,
  updateStudentEnrollment
} from "@/lib/academics";
import { booleanValue, numberOrNull, numberValue } from "@/lib/formPayload";
import type {
  AcademicSession,
  ClassArm,
  Student,
  StudentEnrollment,
  Term
} from "@/types/academics";

const initialValues: FormState = {
  student: "",
  class_arm: "",
  academic_session: "",
  term: "",
  is_active: true
};

export default function StudentEnrollmentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [classArms, setClassArms] = useState<ClassArm[]>([]);
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      const [studentRows, armRows, sessionRows, termRows] = await Promise.all([
        getStudents(),
        getClassArms(),
        getAcademicSessions(),
        getTerms()
      ]);
      setStudents(studentRows);
      setClassArms(armRows);
      setSessions(sessionRows);
      setTerms(termRows);
      setIsLoadingOptions(false);
    }

    void loadOptions();
  }, []);

  const fields = useMemo(
    () => [
      {
        name: "student",
        label: "Student",
        type: "select" as const,
        required: true,
        options: students.map((student) => ({
          value: String(student.id),
          label: `${student.full_name} (${student.email})`
        }))
      },
      {
        name: "class_arm",
        label: "Class arm",
        type: "select" as const,
        required: true,
        options: classArms.map((arm) => ({
          value: String(arm.id),
          label: arm.display_name ?? `${arm.class_level_name ?? ""} ${arm.name}`.trim()
        }))
      },
      {
        name: "academic_session",
        label: "Academic session",
        type: "select" as const,
        required: true,
        options: sessions.map((session) => ({
          value: String(session.id),
          label: session.name
        }))
      },
      {
        name: "term",
        label: "Term",
        type: "select" as const,
        options: terms.map((term) => ({
          value: String(term.id),
          label: `${term.academic_session_name ?? "Session"} - ${term.term_name ?? term.name}`
        })),
        placeholder: "Any term"
      },
      { name: "is_active", label: "Active enrollment", type: "checkbox" as const }
    ],
    [classArms, sessions, students, terms]
  );

  if (isLoadingOptions) {
    return <LoadingState label="Loading enrollment options..." />;
  }

  return (
    <ResourcePage<StudentEnrollment>
      title="Student Enrollments"
      description="Enroll students into class arms for a session and optional term."
      createLabel="New enrollment"
      load={getStudentEnrollments}
      create={(payload) => createStudentEnrollment(payload)}
      update={(id, payload) => updateStudentEnrollment(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        student: String(row.student),
        class_arm: String(row.class_arm),
        academic_session: String(row.academic_session),
        term: row.term ? String(row.term) : "",
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        student: numberValue(values.student),
        class_arm: numberValue(values.class_arm),
        academic_session: numberValue(values.academic_session),
        term: numberOrNull(values.term),
        is_active: booleanValue(values.is_active)
      })}
      fields={fields}
      columns={[
        {
          key: "student",
          header: "Student",
          render: (row) => row.student_name ?? row.student_email ?? row.student
        },
        {
          key: "class_arm",
          header: "Class arm",
          render: (row) => row.class_arm_name ?? row.class_arm
        },
        {
          key: "session",
          header: "Session",
          render: (row) => row.academic_session_name ?? row.academic_session
        },
        {
          key: "term",
          header: "Term",
          render: (row) => row.term_name ?? "Any term"
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
