# MasteryGrid Demo Data

Use the demo seed command to populate a local database with a realistic Nigerian
secondary school setup for pilot testing.

## Run The Seed Command

From the backend directory:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed_demo_data
```

To also create graded student submissions for analytics pages:

```powershell
.\venv\Scripts\python.exe manage.py seed_demo_data --with-submissions
```

The command is idempotent. Running it again updates the same demo records instead
of creating duplicate schools, users, questions, assignments, or submissions.

## Demo Login Credentials

All demo users use this password:

```text
Password123!
```

| Role | Email |
| --- | --- |
| School admin | admin@masterygrid.demo |
| Teacher | teacher@masterygrid.demo |
| Student 1 | student1@masterygrid.demo |
| Student 2 | student2@masterygrid.demo |
| Student 3 | student3@masterygrid.demo |

## Seeded School Setup

- School: MasteryGrid Demo School
- Academic session: 2025/2026
- Term: First Term
- Class level: SS2
- Class arm: Science A
- Subject: Mathematics
- Topics: Quadratic Equations, Simultaneous Equations, Logarithms
- Teacher staff ID: TCH-001
- Student admission numbers: STD-001, STD-002, STD-003

## Recommended Pilot Flow

1. Log in as the school admin and confirm the academic setup, teacher, students,
   teacher assignment, student enrollments, question bank, and published
   assignment.
2. Log in as the teacher and confirm the Mathematics assignment, lesson log,
   question bank access, and assignment detail page.
3. Log in as a student and open the published assignment.
4. If you seeded without submissions, complete and submit the assignment as a
   student, then view the result.
5. If you seeded with submissions, log in as the teacher and review assignment
   results, weak students, weak topics, and individual student performance.
6. Log in as the school admin and review analytics overview, class performance,
   subject performance, teacher activity, weak students, and assignment
   compliance.

## Notes

- The published assignment is "Quadratic Equations Practice".
- It uses five approved Quadratic Equations questions from the seeded question
  bank.
- With `--with-submissions`, Student 1 scores high, Student 2 scores average,
  and Student 3 scores low so analytics pages have useful demo data.
