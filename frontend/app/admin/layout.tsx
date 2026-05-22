import type { ReactNode } from "react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { adminNavItems } from "@/lib/routes";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardLayout
      navItems={adminNavItems}
      allowedRoles={["platform_admin", "school_admin"]}
      sectionLabel="School administration"
    >
      {children}
    </DashboardLayout>
  );
}
