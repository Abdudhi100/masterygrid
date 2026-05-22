"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { FormModal } from "@/components/admin/FormModal";
import {
  ResourceForm,
  type FormState,
  type ResourceField
} from "@/components/admin/ResourceForm";
import {
  ResourceTable,
  type ResourceColumn
} from "@/components/admin/ResourceTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";

type ResourcePageProps<T extends { id: number }> = {
  title: string;
  description: string;
  createLabel: string;
  columns: ResourceColumn<T>[];
  fields: ResourceField[];
  load: () => Promise<T[]>;
  create: (payload: Record<string, unknown>) => Promise<T>;
  update?: (id: number, payload: Record<string, unknown>) => Promise<T>;
  initialValues: FormState;
  toFormValues?: (row: T) => FormState;
  toPayload?: (values: FormState, mode: "create" | "edit") => Record<string, unknown>;
  canCreate?: boolean;
  canEdit?: boolean;
  unavailableMessage?: string;
  filters?: ReactNode;
};

function defaultPayload(values: FormState) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, value === "" ? null : value])
  );
}

export function ResourcePage<T extends { id: number }>({
  title,
  description,
  createLabel,
  columns,
  fields,
  load,
  create,
  update,
  initialValues,
  toFormValues,
  toPayload = defaultPayload,
  canCreate = true,
  canEdit = true,
  unavailableMessage,
  filters
}: ResourcePageProps<T>) {
  const [rows, setRows] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingRow, setEditingRow] = useState<T | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [values, setValues] = useState<FormState>(initialValues);

  const mode = useMemo(() => (editingRow ? "edit" : "create"), [editingRow]);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      setRows(await load());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load records.");
    } finally {
      setIsLoading(false);
    }
  }, [load]);

  useEffect(() => {
    void reload();
  }, [reload]);

  function openCreate() {
    setEditingRow(null);
    setValues(initialValues);
    setIsModalOpen(true);
    setSuccess("");
    setError("");
  }

  function openEdit(row: T) {
    setEditingRow(row);
    setValues(toFormValues ? toFormValues(row) : { ...initialValues });
    setIsModalOpen(true);
    setSuccess("");
    setError("");
  }

  function handleChange(name: string, value: string | boolean) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit() {
    setIsSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const payload = toPayload(values, mode);
      if (editingRow && update) {
        await update(editingRow.id, payload);
        setSuccess(`${title} updated.`);
      } else {
        await create(payload);
        setSuccess(`${title} created.`);
      }
      setIsModalOpen(false);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save record.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title={title}
        description={description}
        actions={
          canCreate ? (
            <Button onClick={openCreate}>{createLabel}</Button>
          ) : undefined
        }
      />

      {unavailableMessage ? (
        <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
          {unavailableMessage}
        </div>
      ) : null}

      {success ? (
        <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-success">
          {success}
        </div>
      ) : null}

      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      {filters ? <Card className="mb-4">{filters}</Card> : null}

      {isLoading ? (
        <LoadingState label={`Loading ${title.toLowerCase()}...`} />
      ) : (
        <ResourceTable
          rows={rows}
          columns={columns}
          getRowId={(row) => row.id}
          onEdit={canEdit && update ? openEdit : undefined}
          emptyTitle={`No ${title.toLowerCase()} yet`}
        />
      )}

      {!canCreate && !rows.length && !isLoading ? (
        <div className="mt-4">
          <EmptyState
            title="Creation unavailable"
            description="This page needs an additional backend endpoint before records can be created here."
          />
        </div>
      ) : null}

      <FormModal
        title={editingRow ? `Edit ${title}` : createLabel}
        isOpen={isModalOpen}
        isSubmitting={isSubmitting}
        submitLabel={editingRow ? "Save changes" : "Create"}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmit}
      >
        <ResourceForm fields={fields} values={values} onChange={handleChange} />
      </FormModal>
    </>
  );
}
