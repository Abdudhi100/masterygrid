"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  createTeacherAssignment,
  getAcademicSessions,
  getClassArms,
  getSubjects,
  getTeacherAssignments,
  getTeachers,
  getTerms,
  updateTeacherAssignment
} from "@/lib/academics";
import { booleanValue, numberOrNull, numberValue } from "@/lib/formPayload";
import type {
  AcademicSession,
  ClassArm,
  Subject,
  Teacher,
  TeacherAssignment,
  Term
} from "@/types/academics";

const initialValues: FormState = {
  teacher: "",
  class_arm: "",
  subject: "",
  academic_session: "",
  term: "",
  is_active: true
};

export default function TeacherAssignmentsPage() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [classArms, setClassArms] = useState<ClassArm[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      const [teacherRows, armRows, subjectRows, sessionRows, termRows] =
        await Promise.all([
          getTeachers(),
          getClassArms(),
          getSubjects(),
          getAcademicSessions(),
          getTerms()
        ]);
      setTeachers(teacherRows);
      setClassArms(armRows);
      setSubjects(subjectRows);
      setSessions(sessionRows);
      setTerms(termRows);
      setIsLoadingOptions(false);
    }

    void loadOptions();
  }, []);

  const fields = useMemo(
    () => [
      {
        name: "teacher",
        label: "Teacher",
        type: "select" as const,
        required: true,
        options: teachers.map((teacher) => ({
          value: String(teacher.id),
          label: `${teacher.full_name} (${teacher.email})`
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
        name: "subject",
        label: "Subject",
        type: "select" as const,
        required: true,
        options: subjects.map((subject) => ({
          value: String(subject.id),
          label: subject.code ? `${subject.name} (${subject.code})` : subject.name
        }))
      },
      {
        name: "academic_session",
        label: "Academic session",
        type: "select" as const,
        options: sessions.map((session) => ({
          value: String(session.id),
          label: session.name
        })),
        placeholder: "Any session"
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
      { name: "is_active", label: "Active assignment", type: "checkbox" as const }
    ],
    [classArms, sessions, subjects, teachers, terms]
  );

  if (isLoadingOptions) {
    return <LoadingState label="Loading teacher assignment options..." />;
  }

  return (
    <ResourcePage<TeacherAssignment>
      title="Teacher Assignments"
      description="Assign teachers to class arms and subjects for the MVP workflow."
      createLabel="New teacher assignment"
      load={getTeacherAssignments}
      create={(payload) => createTeacherAssignment(payload)}
      update={(id, payload) => updateTeacherAssignment(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        teacher: String(row.teacher),
        class_arm: String(row.class_arm),
        subject: String(row.subject),
        academic_session: row.academic_session ? String(row.academic_session) : "",
        term: row.term ? String(row.term) : "",
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        teacher: numberValue(values.teacher),
        class_arm: numberValue(values.class_arm),
        subject: numberValue(values.subject),
        academic_session: numberOrNull(values.academic_session),
        term: numberOrNull(values.term),
        is_active: booleanValue(values.is_active)
      })}
      fields={fields}
      filters={
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted">
            Assign many teachers to classes and subjects with a validated CSV import.
          </p>
          <Link href="/admin/imports/new?type=teacher_assignments">
            <Button variant="secondary">Bulk import teacher assignments</Button>
          </Link>
        </div>
      }
      columns={[
        {
          key: "teacher",
          header: "Teacher",
          render: (row) => row.teacher_name ?? row.teacher_email ?? row.teacher
        },
        {
          key: "class_arm",
          header: "Class arm",
          render: (row) => row.class_arm_name ?? row.class_arm
        },
        {
          key: "subject",
          header: "Subject",
          render: (row) => row.subject_name ?? row.subject
        },
        {
          key: "session",
          header: "Session",
          render: (row) => row.academic_session_name ?? "Any session"
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
