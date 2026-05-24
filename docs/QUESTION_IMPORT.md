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
- `file` - CSV file or ZIP archive

The MVP processes CSV and ZIP imports immediately.

## Preflight Validation

Before creating draft questions, admins can validate a CSV or ZIP file without
creating any question, option, media, import batch, or import row records:

```text
POST /api/question-bank/imports/preflight/
```

Request type:

```text
multipart/form-data
```

Fields:

- `file` - CSV file or ZIP archive
- `source` - optional existing `QuestionSource` ID
- `school` - optional, platform admins only; blank means global validation

Preflight returns a data-quality report with:

- total rows
- valid rows
- invalid rows
- warning rows
- duplicate rows
- missing subjects, class levels, and topics
- missing diagrams
- row-level errors and warnings

Example response shape:

```json
{
  "file_type": "zip",
  "total_rows": 20,
  "valid_rows": 17,
  "invalid_rows": 1,
  "warning_rows": 1,
  "duplicate_rows": 1,
  "can_import": false,
  "summary": {
    "missing_required_fields": 1,
    "missing_correct_option": 1,
    "missing_options": 0,
    "invalid_difficulty": 0,
    "invalid_correct_option": 0,
    "invalid_source_type": 0,
    "duplicate_option_texts": 0,
    "missing_subjects": [],
    "missing_class_levels": [],
    "missing_topics": [],
    "missing_diagrams": 1,
    "duplicate_questions": 1,
    "existing_database_duplicates": 0
  },
  "rows": []
}
```

`valid_rows` includes rows that are valid with warnings. `can_import` is true
only when `invalid_rows` is zero. Duplicate rows follow the normal import
behavior: they are counted separately as duplicates rather than invalid rows.
Warnings do not block import.

Recommended workflow:

1. Upload the file to the preflight endpoint.
2. Review row errors and warnings.
3. Fix the CSV or ZIP if needed.
4. Upload the corrected file to the import endpoint.
5. Review imported draft questions.
6. Approve or reject questions through the normal review workflow.

## Required CSV Columns

```csv
subject,class_level,topic,source_name,source_type,exam_body,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_option,explanation
```

Optional diagram/media columns:

```csv
has_diagram,diagram_file_name,diagram_url,diagram_description,needs_manual_review
```

Example:

```csv
subject,class_level,topic,source_name,source_type,exam_body,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_option,explanation
Mathematics,SS2,Quadratic Equations,JAMB Mathematics,jamb_past_question,JAMB,2024,medium,What is the sum of roots of x^2 - 5x + 6 = 0?,2,3,5,6,C,The sum of roots is -b/a = 5.
```

Example with a diagram URL:

```csv
subject,class_level,topic,source_name,source_type,exam_body,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_option,explanation,has_diagram,diagram_file_name,diagram_url,diagram_description,needs_manual_review
Mathematics,SS2,Quadratic Equations,JAMB Mathematics,jamb_past_question,JAMB,2024,medium,Use the graph to identify the roots.,-2 and 3,-3 and 2,2 and 3,-2 and -3,A,The x-intercepts give the roots.,true,,https://example.com/diagrams/quadratic-roots.png,Graph of a quadratic curve,true
```

## ZIP Imports With Diagrams

ZIP imports use the same CSV columns, but can also attach local diagram files.
The archive must use this structure:

```text
questions.csv
diagrams/
  physics_2025_q1.png
  physics_2025_q2.jpg
  math_2024_q5.webp
```

For each row, `diagram_file_name` may be either:

```text
physics_2025_q1.png
```

or:

```text
diagrams/physics_2025_q1.png
```

Allowed diagram image extensions are:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

ZIP security rules:

- The archive must contain exactly one root-level `questions.csv`.
- The importer does not use `extractall()`.
- Unsafe paths such as `../evil.py`, absolute paths, and backslash traversal are rejected.
- Unexpected non-ignored files outside `questions.csv` and `diagrams/` are rejected.
- Harmless system files such as `__MACOSX/` and `.DS_Store` are ignored.
- Encrypted ZIP entries are not supported.
- Large ZIPs, very large images, and excessive file counts are rejected.

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
- `diagram_url` creates a `QuestionMedia` record linked to the imported draft question.
- ZIP imports can attach a matching `diagram_file_name` as `QuestionMedia.image`.
- If both `diagram_url` and `diagram_file_name` are provided, `diagram_url` is used
  and the ZIP image is ignored with a row warning.
- `has_diagram=true` without `diagram_url` still imports the row as draft, marks the
  question for manual review, and keeps the filename in row `raw_data`.
- For CSV-only imports, `diagram_file_name` remains a manual-review hint.
- For ZIP imports, a missing `diagram_file_name` match does not fail the row; the
  draft question is marked `needs_manual_review=true` and the row gets a
  `warning_message`.
- Diagram questions are never auto-approved.

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
- ZIP `questions.csv` not found: place `questions.csv` at the ZIP root.
- Unsafe ZIP path: remove paths using `..`, absolute paths, or backslash traversal.
- Unsupported diagram type: use `.png`, `.jpg`, `.jpeg`, or `.webp`.
- Duplicate diagram basename: use the full `diagrams/...` path in `diagram_file_name`.
- Diagram file not found: check the filename under `diagrams/`; the question is still
  imported as draft and marked for manual review.
