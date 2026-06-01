"use client";

import Link from "next/link";

import {
  InterventionCategoryBadge,
  InterventionPriorityBadge,
  InterventionStatusBadge
} from "@/components/interventions/InterventionBadges";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import type { StudentIntervention } from "@/types/interventions";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en-NG", { dateStyle: "medium" }).format(date);
}

export function InterventionList({
  interventions,
  baseRole,
  emptyTitle = "No interventions yet",
  emptyDescription = "Intervention records will appear here once they are created."
}: {
  interventions: StudentIntervention[];
  baseRole: "admin" | "teacher";
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  return (
    <DataTable<StudentIntervention>
      data={interventions}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
      columns={[
        {
          key: "title",
          header: "Title",
          render: (row) => (
            <span className="block min-w-[14rem] font-semibold">{row.title}</span>
          )
        },
        {
          key: "student_name",
          header: "Student",
          render: (row) => (
            <div className="min-w-[12rem]">
              <p className="font-semibold">{row.student_name}</p>
              <p className="mt-1 text-xs text-muted">{row.student_class_arm}</p>
            </div>
          )
        },
        {
          key: "category",
          header: "Category",
          render: (row) => <InterventionCategoryBadge category={row.category} />
        },
        {
          key: "priority",
          header: "Priority",
          render: (row) => <InterventionPriorityBadge priority={row.priority} />
        },
        {
          key: "status",
          header: "Status",
          render: (row) => <InterventionStatusBadge status={row.status} />
        },
        {
          key: "due_date",
          header: "Due",
          render: (row) => formatDate(row.due_date)
        },
        {
          key: "assigned_to_name",
          header: "Assigned",
          render: (row) => row.assigned_to_name || "Unassigned"
        },
        {
          key: "updated_at",
          header: "Updated",
          render: (row) => formatDate(row.updated_at)
        },
        {
          key: "action",
          header: "Action",
          render: (row) => (
            <Link
              href={`/${baseRole}/interventions/${row.id}`}
              data-testid="intervention-row"
            >
              <Button variant="secondary">View</Button>
            </Link>
          )
        }
      ]}
    />
  );
}
