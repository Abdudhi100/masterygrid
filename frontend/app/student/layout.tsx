import type { ReactNode } from "react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { studentNavItems } from "@/lib/routes";

export default function StudentLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardLayout
      navItems={studentNavItems}
      allowedRoles={["student"]}
      sectionLabel="Student workspace"
    >
      {children}
    </DashboardLayout>
  );
}
