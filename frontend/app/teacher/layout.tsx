import type { ReactNode } from "react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { teacherNavItems } from "@/lib/routes";

export default function TeacherLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardLayout
      navItems={teacherNavItems}
      allowedRoles={["teacher"]}
      sectionLabel="Teacher workspace"
    >
      {children}
    </DashboardLayout>
  );
}
