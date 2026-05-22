"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

export type ResourceColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
};

type ResourceTableProps<T> = {
  columns: ResourceColumn<T>[];
  rows: T[];
  getRowId: (row: T) => number;
  onEdit?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
};

export function ResourceTable<T>({
  columns,
  rows,
  getRowId,
  onEdit,
  emptyTitle = "No records yet",
  emptyDescription = "Create the first record to begin setting up the school."
}: ResourceTableProps<T>) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-line bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-surface">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-left font-semibold text-muted"
                >
                  {column.header}
                </th>
              ))}
              {onEdit ? (
                <th className="px-4 py-3 text-right font-semibold text-muted">
                  Action
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((row) => (
              <tr key={getRowId(row)} className="hover:bg-surface">
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3 text-ink">
                    {column.render(row)}
                  </td>
                ))}
                {onEdit ? (
                  <td className="px-4 py-3 text-right">
                    <Button variant="secondary" onClick={() => onEdit(row)}>
                      Edit
                    </Button>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
