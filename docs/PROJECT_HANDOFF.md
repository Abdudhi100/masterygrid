# MasteryGrid Project Handoff

## 1. Product Summary
MasteryGrid is an assignment, assessment, question-bank, analytics, and practice platform for Nigerian senior secondary schools. The MVP is database-first: teachers generate assignments from approved question-bank items, students submit online, the system auto-marks, teachers and school admins review analytics, and students can practise independently from approved active questions.

OpenAI is used only as an advisory support layer for existing questions. It must not generate student practice questions directly, and AI output must not be auto-approved.

## 2. Tech Stack
- Backend: Django, Django REST Framework, PostgreSQL
- Auth: JWT via `djangorestframework-simplejwt`
- Backend utilities: `django-environ`, `django-cors-headers`, `django-filter`, `drf-spectacular`, `whitenoise`
- AI provider integration: OpenAI client for reviewed question intelligence only
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Deployment target: Render backend, Render PostgreSQL, Vercel frontend
- Delayed modules: Celery, Redis, payments, parent portal, notifications beyond placeholder, mobile app, direct AI question generation

## 3. Backend Architecture
- Modular monolith under `backend/`
- Settings split: `config/settings/base.py`, `dev.py`, `prod.py`, `test.py`
- API docs:
  - `/api/schema/`
  - `/api/docs/`
- Local apps:
  - `accounts`
  - `schools`
  - `academics`
  - `question_bank`
  - `assignments`
  - `submissions`
  - `practice`
  - `analytics`
  - `notifications`
  - `ai_generation`
  - `common`

## 4. Frontend Architecture
- App Router project under `frontend/`
- Global auth provider in `hooks/useAuth.ts`
- API client in `lib/api.ts`
- Domain API helpers:
  - `lib/academics.ts`
  - `lib/submissions.ts`
  - `lib/practice.ts`
  - `lib/questionBank.ts`
  - `lib/analytics.ts`
  - `lib/aiGeneration.ts`
- Shared UI:
  - `components/ui/*`
  - `components/layout/*`
  - `components/admin/*`
  - `components/question-bank/*`
  - `components/ai-generation/*`
- Role-protected layouts:
  - `app/admin/layout.tsx`
  - `app/teacher/layout.tsx`
  - `app/student/layout.tsx`

## 5. Completed Backend Features
- Split Django settings and production deployment configuration
- Custom email-based `accounts.User`
- JWT login, refresh, and current-user endpoint
- School model and school-scoped user management
- Academic setup APIs:
  - academic sessions, terms, class levels, class arms, subjects, topics
  - teacher class-subject assignments
  - student enrollments
  - lesson logs
- Question bank:
  - question sources
  - question CRUD
  - four-option objective validation
  - draft, approved, rejected, archived statuses
  - approval/rejection/archive workflow
  - approved active question retrieval
- Trusted question import:
  - CSV import batches
  - row-level import records
  - content hashing and duplicate detection
  - imported questions saved as draft only
- Assignment engine:
  - generate assignments from approved active questions only
  - draft, publish, close, archive actions
- Student submissions:
  - start assignment
  - stable question order
  - safe pre-submit question payload
  - answer submission
  - deterministic auto-marking
  - result/correction review
- Teacher analytics:
  - overview
  - assignment results
  - weak students
  - weak topics
  - individual student performance
- School admin analytics:
  - overview
  - class performance
  - subject performance
  - teacher activity
  - weak students
  - assignment compliance
- AI question intelligence:
  - suggestion runs for existing questions
  - topic, difficulty, explanation, duplicate warning, quality warning
  - raw provider response storage controlled by setting
  - human-reviewed apply action
  - no auto-approval
  - no student access
- Student Practice Mode:
  - practice sessions from approved active question-bank questions only
  - safe pre-submit question/options response
  - answer submission
  - auto-marking
  - correction result with explanations after submission
  - practice history
- Demo data seed command
- Deployment docs and production env examples

## 6. Completed Frontend Features
- Login page with JWT storage and role redirects
- Protected dashboards for admin, teacher, and student
- Admin CRUD:
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
- Admin analytics UI:
  - overview
  - class performance
  - subject performance
  - teacher activity
  - weak students
  - assignment compliance
- Teacher workflow:
  - lesson log list and create
  - assignment list and create
  - generate assignment from lesson or topic
  - assignment detail
  - publish, close, archive actions
  - results page
  - weak students
  - weak topics
  - student performance
  - central results page
- Student assignment workflow:
  - assignment list with filters
  - assignment detail
  - attempt page
  - localStorage answer drafts
  - simple countdown timer
  - submit
  - result/correction review
- Question bank UI:
  - admin and teacher question lists
  - create question
  - detail/review page
  - admin approve, reject, archive
  - teacher draft creation/status visibility
  - question sources page
- Question import UI:
  - import history
  - CSV upload
  - template download
  - import detail and row errors
- AI Question Intelligence UI:
  - request suggestions from question detail
  - suggestion history
  - suggestion detail/review
  - manually apply selected fields
- Student Practice Mode UI:
  - practice landing/start form
  - practice history
  - attempt page
  - localStorage answer drafts per student/session
  - result/correction review
- Deployment and demo data docs

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
- `GET/POST /api/question-bank/sources/`
- `GET/POST /api/question-bank/questions/`
- `GET/PATCH /api/question-bank/questions/{id}/`
- `POST /api/question-bank/questions/{id}/approve/`
- `POST /api/question-bank/questions/{id}/reject/`
- `POST /api/question-bank/questions/{id}/archive/`
- `GET /api/question-bank/questions/search-approved/`

Question imports:
- `POST /api/question-bank/imports/`
- `GET /api/question-bank/imports/`
- `GET /api/question-bank/imports/{id}/`
- `GET /api/question-bank/imports/{id}/rows/`

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

Student practice:
- `POST /api/practice/sessions/start/`
- `GET /api/practice/sessions/`
- `GET /api/practice/sessions/{id}/`
- `POST /api/practice/sessions/{id}/submit/`
- `GET /api/practice/sessions/{id}/result/`

Teacher analytics:
- `GET /api/analytics/teacher/overview/`
- `GET /api/analytics/teacher/assignments/{assignment_id}/results/`
- `GET /api/analytics/teacher/weak-students/`
- `GET /api/analytics/teacher/weak-topics/`
- `GET /api/analytics/teacher/students/{student_id}/performance/`

School admin analytics:
- `GET /api/analytics/admin/overview/`
- `GET /api/analytics/admin/class-performance/`
- `GET /api/analytics/admin/subject-performance/`
- `GET /api/analytics/admin/teacher-activity/`
- `GET /api/analytics/admin/weak-students/`
- `GET /api/analytics/admin/assignment-compliance/`

AI question intelligence:
- `POST /api/ai-generation/question-suggestions/`
- `GET /api/ai-generation/question-suggestions/`
- `GET /api/ai-generation/question-suggestions/{id}/`
- `POST /api/ai-generation/question-suggestions/{id}/apply/`

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
- `/admin/question-bank`
- `/admin/question-bank/new`
- `/admin/question-bank/{id}`
- `/admin/question-bank/imports`
- `/admin/question-bank/imports/new`
- `/admin/question-bank/imports/{id}`
- `/admin/question-bank/sources`
- `/admin/question-bank/ai-suggestions`
- `/admin/question-bank/ai-suggestions/{id}`
- `/admin/analytics`
- `/admin/analytics/classes`
- `/admin/analytics/subjects`
- `/admin/analytics/teachers`
- `/admin/analytics/weak-students`
- `/admin/analytics/compliance`

Teacher:
- `/teacher/dashboard`
- `/teacher/lessons`
- `/teacher/lessons/new`
- `/teacher/assignments`
- `/teacher/assignments/new`
- `/teacher/assignments/new?lessonLogId=<id>`
- `/teacher/assignments/{id}`
- `/teacher/assignments/{id}/results`
- `/teacher/results`
- `/teacher/weak-students`
- `/teacher/weak-topics`
- `/teacher/students/{id}/performance`
- `/teacher/question-bank`
- `/teacher/question-bank/new`
- `/teacher/question-bank/{id}`
- `/teacher/question-bank/ai-suggestions`
- `/teacher/question-bank/ai-suggestions/{id}`

Student:
- `/student/dashboard`
- `/student/assignments`
- `/student/assignments/{id}`
- `/student/assignments/{id}/attempt`
- `/student/assignments/{id}/attempt?submissionId=<id>`
- `/student/assignments/{id}/result?submissionId=<id>`
- `/student/practice`
- `/student/practice/{id}`
- `/student/practice/{id}/result`

## 9. Current Data Model Summary
- `School`: tenant root
- `User`: email login, role, optional school
- `TeacherProfile`
- `StudentProfile`
- `AcademicSession`
- `Term`
- `ClassLevel`
- `ClassArm`
- `Subject`
- `Topic`
- `TeacherClassSubjectAssignment`
- `StudentEnrollment`
- `LessonLog`
- `QuestionSource`
- `Question`
- `QuestionOption`
- `QuestionImportBatch`
- `QuestionImportRow`
- `Assignment`
- `AssignmentQuestion`
- `Submission`
- `StudentAnswer`
- `PracticeSession`
- `PracticeSessionQuestion`
- `PracticeAnswer`
- `AIQuestionSuggestionRun`

Analytics are mostly computed directly from transactional tables. No analytics snapshot tables exist yet.

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

## 11. School Scoping and Permission Rules
- `platform_admin` can generally see/manage all schools and global resources.
- `school_admin` can only manage school-scoped users, academics, questions, assignments, imports, and analytics for their own school.
- `teacher` can manage their own lessons and assignments for assigned classes/subjects.
- `teacher` can create draft school questions and request AI suggestions where enabled.
- `student` can only see and submit their own assignments and practice sessions.
- Student practice uses only approved active questions from the database.
- Practice questions include global questions plus questions belonging to the student's school.
- Correct answers and explanations are hidden before assignment/practice submission.
- AI suggestions are not visible to students.
- AI suggestions never auto-approve or directly create student-facing questions.

## 12. Environment Variables
Core backend variables are documented in:
- `backend/.env.example`
- `backend/.env.production.example`

Important AI-related variables:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `AI_GENERATION_ENABLED`
- `AI_STORE_RAW_PROVIDER_RESPONSE`
- `AI_DAILY_REQUEST_LIMIT_PER_USER`
- `AI_ALLOW_TEACHER_SUGGESTIONS`
- `AI_ALLOW_TEACHER_APPLY_SUGGESTIONS`

Frontend production variable:
- `NEXT_PUBLIC_API_BASE_URL`

## 13. Demo Data
Demo data seeding is available:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_demo_data --with-submissions
```

See `docs/DEMO_DATA.md` for credentials and recommended demo flow.

## 14. Deployment
Deployment preparation is complete for:
- Backend: Render or Railway
- Database: managed PostgreSQL
- Frontend: Vercel
- Static files: WhiteNoise
- Media: local for now

See `docs/DEPLOYMENT.md`.

## 15. Important Documentation
- `docs/DEMO_DATA.md`
- `docs/DEPLOYMENT.md`
- `docs/QUESTION_IMPORT.md`
- `docs/AI_QUESTION_INTELLIGENCE.md`

## 16. Known Issues and Limitations
- Local PostgreSQL test DB creation can fail unless the DB user has `CREATEDB`.
- AI suggestion processing is synchronous; Celery/Redis is not yet added.
- OpenAI is used only for advisory question intelligence, not for student practice generation.
- Practice results are stored but not yet integrated into teacher/admin analytics or recommendations.
- Question import supports CSV for now.
- XLSX/JSON import can be added later.
- Media storage is local for now.
- No payments, parent portal, mobile app, or notification delivery system yet.
- Frontend has no automated component/integration test suite yet.
- Student assignment timer is still client-side and simple.

## 17. Useful Backend Commands

```powershell
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py test
```

Focused app tests:

```powershell
.\venv\Scripts\python.exe manage.py test apps.practice
.\venv\Scripts\python.exe manage.py test apps.question_bank
.\venv\Scripts\python.exe manage.py test apps.ai_generation
.\venv\Scripts\python.exe manage.py test apps.analytics
```

If local PostgreSQL cannot create test DBs, a temporary SQLite override has been used for focused tests:

```powershell
$env:DATABASE_URL='sqlite:///test_masterygrid.sqlite3'
.\venv\Scripts\python.exe manage.py test apps.practice
```

## 18. Useful Frontend Commands

```powershell
cd frontend
npm.cmd install
npm.cmd run type-check
npm.cmd run lint
npm.cmd run build
npm.cmd run dev
```

Use `npm.cmd` on Windows PowerShell if `npm.ps1` is blocked by execution policy.

## 19. Recommended Next Steps
1. Integrate `PracticeSession` and `PracticeAnswer` into weak-topic and recommendation analytics.
2. Add student practice insights to the student dashboard.
3. Add teacher/admin aggregate practice analytics only if product scope requires it.
4. Move AI suggestion processing to background jobs with Celery/Redis.
5. Add CSV import preview before processing and support XLSX if needed.
6. Add frontend automated tests for auth redirects and core workflows.
7. Add richer practice filters, such as source type, exam body, and year.
8. Add production monitoring/logging and error reporting.
9. Continue pilot testing with demo data and real school workflows.
