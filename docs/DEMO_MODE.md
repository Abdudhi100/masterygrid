# MasteryGrid Demo Mode

Demo mode adds a guarded "Try Demo" panel to the login page and a walkthrough
page for school demos, investor reviews, and product walkthroughs.

Demo mode is frontend-only and must be explicitly enabled:

```env
NEXT_PUBLIC_ENABLE_DEMO_MODE=true
```

Keep it disabled for normal production deployments.

## Enable Locally

Frontend `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
NEXT_PUBLIC_ENABLE_DEMO_MODE=true
```

Then start the app:

```powershell
cd frontend
npm.cmd run dev
```

For a production-style local build, set the flag before building:

```powershell
cd frontend
$env:NEXT_PUBLIC_ENABLE_DEMO_MODE="true"
npm.cmd run build
npm.cmd run start
```

## Seed Demo Data

From the backend directory:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed_demo_data --with-submissions
```

The seed command is idempotent and creates the demo school, users, academics,
question bank, assignment, practice-ready questions, and analytics evidence.

## Demo Credentials

All seeded demo users use:

```text
Password123!
```

| Role | Email |
| --- | --- |
| School Admin | admin@masterygrid.demo |
| Teacher | teacher@masterygrid.demo |
| Student 1 | student1@masterygrid.demo |
| Student 2 | student2@masterygrid.demo |
| Student 3 | student3@masterygrid.demo |

When demo mode is enabled, the login page shows a **Try Demo** panel. Clicking a
demo user only fills the email and password fields. The visitor must still click
**Sign in**.

## Walkthrough

Open:

```text
/demo-guide
```

Recommended flow:

1. Sign in as School Admin and review setup wizard, question bank, admin
   dashboard, interventions, and audit logs.
2. Sign out, sign in as Teacher, inspect the teacher dashboard, create or view
   an assignment, and open remediation.
3. Sign out, sign in as a Student, practice questions, view learning path, and
   review practice analytics.
4. Return as School Admin to show intervention follow-up and whole-school risk.

When demo mode is enabled, the role dashboards show an **Open Demo Guide** CTA.

## E2E Demo Test

The demo test is separate from the normal full suite because it requires the
demo flag and seeded demo credentials.

```powershell
cd frontend
$env:NEXT_PUBLIC_ENABLE_DEMO_MODE="true"
npm.cmd run e2e -- e2e/tests/22-demo-mode-flow.spec.ts
```

If you run against a production build, rebuild the frontend with
`NEXT_PUBLIC_ENABLE_DEMO_MODE=true` before starting the server.

## Security Notes

- Keep `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` in real production.
- Do not use demo credentials for a real school tenant.
- Do not add auto-login behavior for demo users.
- Do not expose the demo panel unless the environment flag is explicitly true.
- The flag is public because it controls frontend UI only; backend permissions
  and authentication remain unchanged.
