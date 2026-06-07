import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { APP_NAME } from "@/lib/constants";
import { demoAccounts, isDemoModeEnabled } from "@/lib/demoMode";

const walkthroughSections = [
  {
    title: "School admin walkthrough",
    account: "School Admin",
    steps: [
      { label: "Check setup wizard", href: "/admin/setup" },
      { label: "View question bank", href: "/admin/question-bank" },
      { label: "Open admin dashboard", href: "/admin/dashboard" },
      { label: "Review interventions", href: "/admin/interventions" }
    ]
  },
  {
    title: "Teacher walkthrough",
    account: "Teacher",
    steps: [
      { label: "Open teacher dashboard", href: "/teacher/dashboard" },
      { label: "Create assignment", href: "/teacher/assignments/new" },
      { label: "Review results", href: "/teacher/results" },
      { label: "View remediation", href: "/teacher/remediation" }
    ]
  },
  {
    title: "Student walkthrough",
    account: "Student 1, Student 2, or Student 3",
    steps: [
      { label: "Open student dashboard", href: "/student/dashboard" },
      { label: "Practice questions", href: "/student/practice" },
      { label: "View learning path", href: "/student/learning-path" },
      { label: "Check practice analytics", href: "/student/practice/analytics" }
    ]
  }
];

export default function DemoGuidePage() {
  if (!isDemoModeEnabled) {
    return (
      <main className="min-h-screen bg-surface px-4 py-10">
        <div className="mx-auto max-w-3xl">
          <Card>
            <p className="text-sm font-semibold text-brand-700">{APP_NAME}</p>
            <h1 className="mt-3 text-2xl font-semibold text-ink">
              Demo guide is disabled
            </h1>
            <p className="mt-3 text-sm leading-6 text-muted">
              Enable `NEXT_PUBLIC_ENABLE_DEMO_MODE=true` in a local, staging, or
              demo environment to show demo credentials and walkthrough steps.
            </p>
            <Link href="/login" className="mt-5 inline-block">
              <Button>Back to Login</Button>
            </Link>
          </Card>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-surface px-4 py-10">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-brand-700">{APP_NAME}</p>
            <h1 className="mt-3 text-3xl font-semibold text-ink">
              Demo Guide
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              A guided route through the seeded demo school for school leaders,
              teachers, investors, and reviewers.
            </p>
          </div>
          <Link href="/login">
            <Button>Open Login</Button>
          </Link>
        </div>

        <section className="grid gap-4 lg:grid-cols-5">
          {demoAccounts.map((account) => (
            <Card key={account.key} className="h-full">
              <p className="text-sm font-semibold text-ink">{account.label}</p>
              <p className="mt-2 break-words text-sm text-brand-700">
                {account.email}
              </p>
              <p className="mt-2 text-xs leading-5 text-muted">
                Password: {account.password}
              </p>
              <p className="mt-3 text-sm leading-6 text-muted">
                {account.description}
              </p>
            </Card>
          ))}
        </section>

        <section className="mt-6 grid gap-4 lg:grid-cols-3">
          {walkthroughSections.map((section) => (
            <Card key={section.title} className="h-full">
              <p className="text-sm font-semibold text-brand-700">
                {section.account}
              </p>
              <h2 className="mt-2 text-lg font-semibold text-ink">
                {section.title}
              </h2>
              <div className="mt-4 space-y-3">
                {section.steps.map((step, index) => (
                  <Link
                    key={step.href}
                    href={step.href}
                    className="flex items-center justify-between gap-3 rounded-md border border-line bg-white px-3 py-2 transition hover:border-brand-200 hover:bg-brand-50/40"
                  >
                    <span className="text-sm font-semibold text-ink">
                      {index + 1}. {step.label}
                    </span>
                    <span className="text-sm text-brand-700">Open</span>
                  </Link>
                ))}
              </div>
            </Card>
          ))}
        </section>

        <Card className="mt-6">
          <h2 className="text-lg font-semibold text-ink">Recommended demo flow</h2>
          <ol className="mt-3 space-y-2 text-sm leading-6 text-muted">
            <li>1. Sign in as School Admin and review setup, question bank, analytics, and interventions.</li>
            <li>2. Sign out, sign in as Teacher, create or inspect an assignment, and open remediation.</li>
            <li>3. Sign out, sign in as a Student, complete practice, and review the learning path.</li>
            <li>4. Return as School Admin to show dashboards, audit logs, and intervention follow-up.</li>
          </ol>
        </Card>
      </div>
    </main>
  );
}
