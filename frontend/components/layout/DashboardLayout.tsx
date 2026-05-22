"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { LoadingState } from "@/components/ui/LoadingState";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { APP_NAME } from "@/lib/constants";
import { useRequireAuth } from "@/hooks/useAuth";
import type { NavItem } from "@/types/common";
import type { UserRole } from "@/types/auth";

type DashboardLayoutProps = {
  children: ReactNode;
  navItems: NavItem[];
  allowedRoles: UserRole[];
  sectionLabel: string;
};

export function DashboardLayout({
  children,
  navItems,
  allowedRoles,
  sectionLabel
}: DashboardLayoutProps) {
  const pathname = usePathname();
  const { status, isAuthorized } = useRequireAuth(allowedRoles);
  const activeHref = [...navItems]
    .filter(
      (item) => pathname === item.href || pathname.startsWith(`${item.href}/`)
    )
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;

  if (status === "loading") {
    return (
      <main className="min-h-screen bg-surface p-6">
        <LoadingState label="Checking your session..." />
      </main>
    );
  }

  if (!isAuthorized) {
    return (
      <main className="min-h-screen bg-surface p-6">
        <LoadingState label="Redirecting..." />
      </main>
    );
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar items={navItems} sectionLabel={sectionLabel} />
      <div className="min-w-0 flex-1">
        <Topbar />
        <div className="border-b border-line bg-white px-4 py-3 lg:hidden">
          <p className="text-base font-bold text-ink">{APP_NAME}</p>
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {navItems.map((item) => {
              const isActive = item.href === activeHref;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold ${
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "bg-surface text-muted"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
