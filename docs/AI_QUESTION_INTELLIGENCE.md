# AI Question Intelligence

MasteryGrid keeps the reviewed question bank as the source of truth. AI is only a
support layer for metadata and quality suggestions on existing questions.

This feature does not generate student-facing questions, does not approve
questions, and does not change assignment generation. Any AI-generated question
work added later must save draft questions for human review.

## What AI Can Suggest

- Topic classification against existing topics only
- Difficulty estimate: `easy`, `medium`, or `hard`
- Explanation text
- Duplicate or quality warnings

Suggestions are stored in `AIQuestionSuggestionRun` records. A suggestion run does
not modify the `Question` until an authorized user explicitly applies selected
fields.

## Environment Variables

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=60
AI_GENERATION_ENABLED=True
AI_STORE_RAW_PROVIDER_RESPONSE=False
AI_DAILY_REQUEST_LIMIT_PER_USER=20
AI_ALLOW_TEACHER_SUGGESTIONS=True
AI_ALLOW_TEACHER_APPLY_SUGGESTIONS=False
```

Keep `AI_STORE_RAW_PROVIDER_RESPONSE=False` unless raw provider payloads are
needed for debugging.

## Endpoints

Request a suggestion:

```http
POST /api/ai-generation/question-suggestions/
```

```json
{
  "question": 1,
  "suggestion_type": "topic_difficulty_explanation"
}
```

List visible suggestion runs:

```http
GET /api/ai-generation/question-suggestions/
```

View one suggestion run:

```http
GET /api/ai-generation/question-suggestions/{id}/
```

Apply selected fields:

```http
POST /api/ai-generation/question-suggestions/{id}/apply/
```

```json
{
  "fields_to_apply": ["topic", "difficulty", "explanation"]
}
```

## Permissions

- `platform_admin`: can request and apply suggestions for global and school
  questions.
- `school_admin`: can request and apply suggestions for own-school questions.
- `teacher`: can request suggestions for own-school questions when enabled.
  Teachers cannot apply suggestions unless
  `AI_ALLOW_TEACHER_APPLY_SUGGESTIONS=True`.
- `student`: cannot request, view, or apply AI suggestions.

## Safety Rules

- AI suggestions never approve questions.
- AI suggestions never create topics automatically.
- Topic suggestions are matched to existing active topics for the question's
  subject and class level.
- Question status is preserved when suggestions are applied.
- Raw provider responses are not stored unless explicitly enabled.
