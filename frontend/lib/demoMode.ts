export const isDemoModeEnabled =
  process.env.NEXT_PUBLIC_ENABLE_DEMO_MODE === "true";

export const DEMO_PASSWORD = "Password123!";

export type DemoAccount = {
  key: string;
  label: string;
  email: string;
  password: string;
  description: string;
};

export const demoAccounts: DemoAccount[] = [
  {
    key: "school-admin",
    label: "School Admin",
    email: "admin@masterygrid.demo",
    password: DEMO_PASSWORD,
    description: "School setup, imports, analytics, interventions, and audit logs."
  },
  {
    key: "teacher",
    label: "Teacher",
    email: "teacher@masterygrid.demo",
    password: DEMO_PASSWORD,
    description: "Assignments, submissions, remediation, weak topics, and notes."
  },
  {
    key: "student1",
    label: "Student 1",
    email: "student1@masterygrid.demo",
    password: DEMO_PASSWORD,
    description: "High-performing student profile with completed work."
  },
  {
    key: "student2",
    label: "Student 2",
    email: "student2@masterygrid.demo",
    password: DEMO_PASSWORD,
    description: "Average student profile for comparison."
  },
  {
    key: "student3",
    label: "Student 3",
    email: "student3@masterygrid.demo",
    password: DEMO_PASSWORD,
    description: "Student with support needs for analytics and interventions."
  }
];
