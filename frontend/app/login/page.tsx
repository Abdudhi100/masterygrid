"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { APP_NAME } from "@/lib/constants";
import { dashboardPathForRole } from "@/lib/routes";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, status, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated" && user) {
      router.replace(dashboardPathForRole(user.role));
    }
  }, [router, status, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const currentUser = await login({ email, password });
      const next = searchParams.get("next");
      const safeNext = next?.startsWith("/") && !next.startsWith("//") ? next : null;
      router.replace(safeNext || dashboardPathForRole(currentUser.role));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to sign in. Check your details and try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-surface lg:grid-cols-[1.05fr_0.95fr]">
      <section className="flex items-center px-6 py-10 sm:px-10 lg:px-16">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <p className="text-2xl font-bold tracking-normal text-ink">{APP_NAME}</p>
            <h1 className="mt-8 text-3xl font-semibold tracking-normal text-ink">
              Sign in to your workspace
            </h1>
            <p className="mt-3 text-sm leading-6 text-muted">
              AI-powered assignment and assessment platform for smarter schools.
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Email address"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            {error ? (
              <div className="rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-danger">
                {error}
              </div>
            ) : null}
            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Sign in
            </Button>
          </form>
        </div>
      </section>

      <section className="hidden border-l border-line bg-white p-10 lg:flex lg:items-center">
        <div className="mx-auto max-w-lg">
          <div className="rounded-lg border border-line bg-surface p-8 shadow-soft">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-700">
              Mastery intelligence
            </p>
            <h2 className="mt-5 text-4xl font-semibold tracking-normal text-ink">
              See what was taught, answered, missed, and mastered.
            </h2>
            <p className="mt-5 text-base leading-7 text-muted">
              MasteryGrid helps school leaders and teachers turn objective
              assignments into practical evidence for better support.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-surface text-sm font-medium text-muted">
          Loading sign in...
        </main>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
