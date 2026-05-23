# Practice Analytics and Recommendations

Practice analytics are database-first. They use only submitted practice sessions
from `apps.practice` and approved active question-bank availability. They do not
call OpenAI, generate questions, or expose one student's data to another student.

## Endpoints

All endpoints require an authenticated student user:

- `GET /api/practice/analytics/summary/`
- `GET /api/practice/analytics/subjects/`
- `GET /api/practice/analytics/topics/`
- `GET /api/practice/analytics/weak-topics/`
- `GET /api/practice/analytics/strong-topics/`
- `GET /api/practice/analytics/recommendations/`
- `GET /api/practice/analytics/dashboard/`

Teacher, admin, anonymous, and cross-student access is blocked for the MVP.

## Computation Rules

Only `PracticeSession.status = submitted` is included. In-progress and abandoned
sessions are ignored.

The summary uses weighted performance:

```text
overall_average_percentage = total_score / total_marks * 100
```

Subject and topic performance use the same weighted score/marks approach.
Topic analytics exclude sessions that do not have a topic.

Topic strength levels:

- `strong`: average percentage is 70 or above
- `average`: average percentage is 50 to 69
- `weak`: average percentage is below 50

Weak topics require average percentage below 50 and either at least 5 answered
questions or at least 2 submitted sessions.

Strong topics require average percentage of 70 or above and either at least 5
answered questions or at least 2 submitted sessions.

## Recommendation Logic

Recommendations are generated from database performance and approved active
question availability.

Priority order:

1. Weak practised topics with approved active questions.
2. Average practised topics with approved active questions.
3. Unpractised topics that have approved active questions.

Availability counts only `question_bank.Question` records where:

- `status = approved`
- `is_active = true`
- topic and subject match
- question is global or belongs to the student's school

Recommended difficulty:

- below 50 percent: `easy`
- 50 to 69 percent: `medium`
- 70 percent and above: `hard`
- no history: `easy`

Topics with zero approved active questions are not recommended.

## No Practice History

Students with no submitted practice sessions receive safe zero/null summary
values, empty performance arrays, and the message:

```text
Complete a practice session to unlock personalized analytics.
```

If approved active questions exist, the recommendations endpoint can still
suggest unpractised topics.

## Future AI Extension

AI may later turn these database recommendations into friendlier study advice,
but AI should remain advisory. Practice question selection and analytics should
continue to use trusted database questions and submitted student performance.
