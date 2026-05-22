# MasteryGrid Project Handoff

## 1. Product Summary
MasteryGrid is an AI-powered assignment and assessment platform for Nigerian senior secondary schools. The MVP focuses on JAMB-style objective questions: school admins set up academic structure, teachers log taught topics, teachers generate objective assignments from approved question bank items, students answer online, the system auto-marks, and teachers/school admins review performance.

## 2. Tech Stack
- Backend: Django, Django REST Framework, PostgreSQL
- Auth: JWT via `djangorestframework-simplejwt`
- Backend utilities: `django-environ`, `django-cors-headers`, `django-filter`, `drf-spectacular`, `whitenoise`
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Future delayed modules: AI generation, Celery, Redis, SMS, billing, parent portal, advanced proctoring

## 3. Backend Architecture
- Modular monolith under `backend/`
- Settings split: `config/settings/base.py`, `dev.py`, `prod.py`, `test.py`
- Local apps under `backend/apps/`
- Apps:
  - `accounts`
  - `schools`
  - `academics`
  - `question_bank`
  - `assignments`
  - `submissions`
  - `analytics`
  - `notifications`
  - `ai_generation`
  - `common`
- API docs:
  - `/api/schema/`
  - `/api/docs/`

## 4. Frontend Architecture
- App Router project under `frontend/`
- Global auth provider in `hooks/useAuth.ts`
- API client in `lib/api.ts`
- Domain API helpers:
  - `lib/academics.ts`
  - `lib/submissions.ts`
- Shared UI components:
  - `components/ui/*`
  - `components/layout/*`
  - `components/admin/*`
- Role-protected layouts:
  - `app/admin/layout.tsx`
  - `app/teacher/layout.tsx`
  - `app/student/layout.tsx`

## 5. Completed Backend Features
- Split Django settings and project foundation
- Custom email-based `accounts.User`
- JWT login, refresh, and current-user endpoint
- School model
- Academics models and APIs:
  - academic sessions, terms, class levels, class arms, subjects, topics
  - teacher class-subject assignments
  - student enrollments
  - lesson logs
- Question bank foundation:
  - question sources, questions, four-option JAMB MVP validation, approval flow
- Assignment engine:
  - assignment generation from approved questions
  - draft/publish/close/archive actions
- Student submissions:
  - start assignment
  - stable question order
  - deterministic auto-marking
  - results with corrections
- Analytics:
  - teacher overview, assignment results, weak students/topics, student performance
  - school admin overview, class/subject performance, teacher activity, weak students, assignment compliance
- School-scoped user management:
  - teacher/student lists
  - teacher/student profile create/update
  - enhanced teacher/student registration with profile fields

## 6. Completed Frontend Features
- Next.js/Tailwind foundation
- Login page with JWT storage and role redirects
- Protected dashboards for admin, teacher, student
- Admin CRUD foundation:
  - academic sessions
  - terms
  - class levels
  - class arms
  - subjects
  - topics
  - teachers
  - students
  - teacher assignments
  - student enrollments
- Teacher workflow:
  - lesson log list
  - new lesson log form
  - assignment list
  - generate assignment from lesson or manual topic
  - draft preview
  - publish/close/archive actions
  - assignment detail
  - results placeholder
- Student workflow:
  - assignment list with filters
  - assignment pre-start detail
  - start/continue attempt
  - answer selection
  - localStorage answer draft
  - simple countdown timer
  - submit and auto-mark
  - result/correction review

## 7. Important Backend API Endpoints
Auth and users:
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`
- `POST /api/auth/register/`
- `GET /api/auth/teachers/`
- `GET /api/auth/students/`
- `GET/POST/PATCH /api/auth/teacher-profiles/`
- `GET/POST/PATCH /api/auth/student-profiles/`

Academics:
- `/api/academics/academic-sessions/`
- `/api/academics/terms/`
- `/api/academics/class-levels/`
- `/api/academics/class-arms/`
- `/api/academics/subjects/`
- `/api/academics/topics/`
- `/api/academics/teacher-assignments/`
- `/api/academics/student-enrollments/`
- `/api/academics/lesson-logs/`

Question bank:
- `/api/question-bank/sources/`
- `/api/question-bank/questions/`
- `/api/question-bank/questions/{id}/approve/`
- `/api/question-bank/questions/{id}/reject/`
- `/api/question-bank/questions/{id}/archive/`

Assignments:
- `GET /api/assignments/`
- `GET /api/assignments/{id}/`
- `POST /api/assignments/generate-from-topic/`
- `POST /api/assignments/{id}/publish/`
- `POST /api/assignments/{id}/close/`
- `POST /api/assignments/{id}/archive/`

Submissions:
- `GET /api/submissions/my-assignments/`
- `POST /api/submissions/start-assignment/`
- `GET /api/submissions/{id}/`
- `POST /api/submissions/{id}/submit/`
- `GET /api/submissions/{id}/result/`

Analytics:
- `/api/analytics/teacher/overview/`
- `/api/analytics/teacher/assignments/{assignment_id}/results/`
- `/api/analytics/teacher/weak-students/`
- `/api/analytics/teacher/weak-topics/`
- `/api/analytics/teacher/students/{student_id}/performance/`
- `/api/analytics/admin/overview/`
- `/api/analytics/admin/class-performance/`
- `/api/analytics/admin/subject-performance/`
- `/api/analytics/admin/teacher-activity/`
- `/api/analytics/admin/weak-students/`
- `/api/analytics/admin/assignment-compliance/`

## 8. Important Frontend Routes
Auth:
- `/login`

Admin:
- `/admin/dashboard`
- `/admin/academic-sessions`
- `/admin/terms`
- `/admin/class-levels`
- `/admin/class-arms`
- `/admin/subjects`
- `/admin/topics`
- `/admin/teachers`
- `/admin/students`
- `/admin/teacher-assignments`
- `/admin/student-enrollments`

Teacher:
- `/teacher/dashboard`
- `/teacher/lessons`
- `/teacher/lessons/new`
- `/teacher/assignments`
- `/teacher/assignments/new`
- `/teacher/assignments/new?lessonLogId=<id>`
- `/teacher/assignments/{id}`
- `/teacher/assignments/{id}/results`

Student:
- `/student/dashboard`
- `/student/assignments`
- `/student/assignments/{id}`
- `/student/assignments/{id}/attempt`
- `/student/assignments/{id}/attempt?submissionId=<id>`
- `/student/assignments/{id}/result?submissionId=<id>`

## 9. Current Data Model Summary
- `School`: school tenant root
- `User`: email login, role, optional school
- `TeacherProfile`: teacher metadata
- `StudentProfile`: student metadata
- `AcademicSession`, `Term`
- `ClassLevel`, `ClassArm`
- `Subject`, `Topic`
- `TeacherClassSubjectAssignment`: teacher-class-subject mapping
- `StudentEnrollment`: student-class/session mapping
- `LessonLog`: taught topic record
- `QuestionSource`, `Question`, `QuestionOption`
- `Assignment`, `AssignmentQuestion`
- `Submission`, `StudentAnswer`
- Analytics are computed directly from existing tables; no analytics snapshot tables yet.

## 10. Authentication and User Roles
Roles:
- `platform_admin`
- `school_admin`
- `teacher`
- `student`

Frontend redirects:
- `platform_admin` -> `/admin/dashboard`
- `school_admin` -> `/admin/dashboard`
- `teacher` -> `/teacher/dashboard`
- `student` -> `/student/dashboard`

JWT tokens are stored in browser `localStorage`.

## 11. School-Scoping and Permission Rules
- `platform_admin` can generally see/manage all schools.
- `school_admin` can only manage users, academics, assignments, and analytics for their own school.
- `teacher` can only manage their own lesson logs and assignments for assigned class arms/subjects.
- `student` can only see and submit their own published assignments.
- Cross-school access should be blocked at queryset and validation layers.
- Global subjects/topics/questions are allowed where models support nullable `school`.

## 12. Known Issues or Limitations
- PostgreSQL test DB creation currently fails locally unless the DB user has `CREATEDB`.
- Teacher assignment detail preview does not show answer options because assignment serializer currently returns question text/difficulty only.
- Teacher results UI is only a placeholder.
- Student timer is simple client-side countdown; no server-time sync yet.
- Student attempt auto-submit only submits when all questions are answered.
- Question bank admin/teacher frontend UI is not built yet.
- Full teacher result analytics frontend is not built yet.
- AI generation app exists as placeholder only.
- No Celery/Redis/background jobs yet.

## 13. Environment Setup Commands
Backend:
- `cd backend`
- Create/activate virtual environment if needed.
- `pip install -r requirements/dev.txt`
- Create `.env` from `.env.example`
- Ensure PostgreSQL database/user exists.
- `python manage.py migrate`
- `python manage.py createsuperuser`
- `python manage.py runserver`

Frontend:
- `cd frontend`
- `npm.cmd install`
- Create `.env.local` with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api`
- `npm.cmd run dev`

Use `npm.cmd` on Windows PowerShell if `npm.ps1` is blocked by execution policy.

## 14. Test and Build Commands
Backend:
- `cd backend`
- `.\venv\Scripts\python manage.py check`
- `.\venv\Scripts\python manage.py makemigrations --check --dry-run`
- `.\venv\Scripts\python manage.py test apps.accounts`
- `.\venv\Scripts\python manage.py test apps.analytics`
- `.\venv\Scripts\python manage.py test`

Frontend:
- `cd frontend`
- `npm.cmd run type-check`
- `npm.cmd run lint`
- `npm.cmd run build`

## 15. Recommended Next Steps
1. Build teacher results frontend for `/teacher/assignments/{id}/results` using `/api/analytics/teacher/assignments/{assignment_id}/results/`.
2. Build question bank frontend for admin/teacher question creation, nested options, approval, and filtering.
3. Improve teacher assignment preview to include options if backend should expose safe teacher-only option data.
4. Add frontend edit flows for teacher/student profiles if needed after creation.
5. Add stronger frontend handling for late/closed assignment states.
6. Add seed/demo data management command for local testing.
7. Add comprehensive backend tests once PostgreSQL test DB permissions are fixed.
8. Add frontend component/integration tests for auth redirects and core workflows.
9. Polish UI responsiveness and empty-state wording after real user testing.
10. Only after MVP workflow is stable, begin AI question generation design.
