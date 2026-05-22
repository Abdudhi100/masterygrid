"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { ROLE_LABELS } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-white/90 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-sm font-semibold text-ink">
            {user?.full_name ?? "MasteryGrid"}
          </p>
          <p className="text-xs font-medium text-muted">
            {user ? ROLE_LABELS[user.role] : "Loading profile"}
          </p>
        </div>
        <Button variant="secondary" onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
