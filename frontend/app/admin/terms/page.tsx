"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  createTerm,
  getAcademicSessions,
  getTerms,
  updateTerm
} from "@/lib/academics";
import { booleanValue, numberValue, stringValue } from "@/lib/formPayload";
import type { AcademicSession, Term } from "@/types/academics";

const initialValues: FormState = {
  academic_session: "",
  name: "first",
  starts_at: "",
  ends_at: "",
  is_active: false
};

export default function TermsPage() {
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      setSessions(await getAcademicSessions());
      setIsLoadingOptions(false);
    }
    void loadOptions();
  }, []);

  const fields = useMemo(
    () => [
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
        name: "name",
        label: "Term",
        type: "select" as const,
        required: true,
        options: [
          { value: "first", label: "First Term" },
          { value: "second", label: "Second Term" },
          { value: "third", label: "Third Term" }
        ]
      },
      { name: "starts_at", label: "Starts at", type: "date" as const, required: true },
      { name: "ends_at", label: "Ends at", type: "date" as const, required: true },
      { name: "is_active", label: "Active term", type: "checkbox" as const }
    ],
    [sessions]
  );

  const load = useCallback(() => getTerms(), []);

  if (isLoadingOptions) {
    return <LoadingState label="Loading academic sessions..." />;
  }

  return (
    <ResourcePage<Term>
      title="Terms"
      description="Create and manage first, second, and third terms inside an academic session."
      createLabel="New term"
      load={load}
      create={(payload) => createTerm(payload)}
      update={(id, payload) => updateTerm(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        academic_session: String(row.academic_session),
        name: row.name,
        starts_at: row.starts_at,
        ends_at: row.ends_at,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        academic_session: numberValue(values.academic_session),
        name: stringValue(values.name),
        starts_at: stringValue(values.starts_at),
        ends_at: stringValue(values.ends_at),
        is_active: booleanValue(values.is_active)
      })}
      fields={fields}
      columns={[
        { key: "name", header: "Term", render: (row) => row.term_name ?? row.name },
        {
          key: "session",
          header: "Session",
          render: (row) => row.academic_session_name ?? row.academic_session
        },
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
