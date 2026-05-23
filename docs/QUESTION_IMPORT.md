# Trusted Question Import

MasteryGrid imports trusted JAMB/past-exam questions into the existing question
bank as draft questions. Imported questions must still be reviewed and approved
before assignments can use them.

## Endpoint

```text
POST /api/question-bank/imports/
```

Request type:

```text
multipart/form-data
```

Fields:

- `title` - import batch title
- `source` - optional existing `QuestionSource` ID
- `school` - optional, platform admins only; blank means global import
- `file` - CSV file

The MVP processes CSV imports immediately.

## Required CSV Columns

```csv
subject,class_level,topic,source_name,source_type,exam_body,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_option,explanation
```

Example:

```csv
subject,class_level,topic,source_name,source_type,exam_body,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_option,explanation
Mathematics,SS2,Quadratic Equations,JAMB Mathematics,jamb_past_question,JAMB,2024,medium,What is the sum of roots of x^2 - 5x + 6 = 0?,2,3,5,6,C,The sum of roots is -b/a = 5.
```

## Valid Values

`source_type` must be one of:

- `jamb_past_question`
- `waec_past_question`
- `neco_past_question`
- `teacher_created`
- `ai_generated`
- `school_created`

`difficulty` must be:

- `easy`
- `medium`
- `hard`

`correct_option` must be:

- `A`
- `B`
- `C`
- `D`

## Import Rules

- Imported questions are always saved with `status=draft`.
- Imported questions are never auto-approved.
- Imported questions are created as `is_active=true`.
- `subject`, `class_level`, and `topic` must already exist.
- `topic` must match the selected subject and class level.
- Every row must have exactly four option texts.
- Exactly one option must be marked correct.
- Duplicate option text in the same question is rejected.
- Exact duplicate questions are marked as duplicate using a content hash.

## Review Workflow

1. Import the CSV.
2. Open the import batch and review failed or duplicate rows.
3. Review imported draft questions in the question bank.
4. School admin or platform admin approves/rejects questions.
5. Assignment generation can use only approved active questions.

Existing review endpoints:

```text
POST /api/question-bank/questions/{id}/approve/
POST /api/question-bank/questions/{id}/reject/
POST /api/question-bank/questions/{id}/archive/
```

## Import History

```text
GET /api/question-bank/imports/
GET /api/question-bank/imports/{id}/
GET /api/question-bank/imports/{id}/rows/
```

## Approved Question Retrieval

```text
GET /api/question-bank/questions/search-approved/
```

Supported filters:

- `subject`
- `topic`
- `class_level`
- `difficulty`
- `source_type`
- `exam_body`
- `year`
- `count`
- `random`

This endpoint returns approved active database questions only. It does not call
AI and does not return draft, rejected, archived, or inactive questions.

## Common Errors

- Missing column: add all required CSV headers exactly as listed.
- Subject not found: create the subject before import.
- Class level not found: create the class level before import.
- Topic not found: create the topic and ensure it matches subject/class level.
- Invalid difficulty: use `easy`, `medium`, or `hard`.
- Invalid correct option: use `A`, `B`, `C`, or `D`.
- Duplicate row: the same normalized question/options already exist.
