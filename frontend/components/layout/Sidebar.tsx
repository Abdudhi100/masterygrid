"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { APP_NAME } from "@/lib/constants";
import type { NavItem } from "@/types/common";

type SidebarProps = {
  items: NavItem[];
  sectionLabel: string;
};

export function Sidebar({ items, sectionLabel }: SidebarProps) {
  const pathname = usePathname();
  const activeHref = [...items]
    .filter(
      (item) => pathname === item.href || pathname.startsWith(`${item.href}/`)
    )
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;

  return (
    <aside className="hidden w-72 shrink-0 border-r border-line bg-white lg:flex lg:flex-col">
      <div className="border-b border-line px-6 py-5">
        <p className="text-xl font-bold tracking-normal text-ink">{APP_NAME}</p>
        <p className="mt-1 text-sm font-medium text-muted">{sectionLabel}</p>
      </div>
      <nav className="flex-1 space-y-1 px-4 py-5">
        {items.map((item) => {
          const isActive = item.href === activeHref;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-2.5 text-sm font-semibold transition ${
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-muted hover:bg-surface hover:text-ink"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
