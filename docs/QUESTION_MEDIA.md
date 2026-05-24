# Question Media and Diagrams

MasteryGrid supports optional question diagrams through `QuestionMedia` records
linked to existing question-bank questions. Questions can have zero, one, or many
media items, although the current UI can treat the first active primary image as
the main diagram.

## Model Shape

`QuestionMedia` stores:

- `question`
- `media_type` currently `image`
- `image` for uploaded files
- `external_url` for diagram URLs
- `original_filename`
- `description`
- `alt_text`
- `caption`
- `display_order`
- `is_primary`
- `is_active`
- `needs_manual_review`
- `created_by`

`Question` also has:

- `has_diagram`
- `diagram_description`
- `needs_manual_review`

If a question has active media, `has_diagram` is kept true. Imported questions
that reference a missing diagram file can also keep `has_diagram=true` while
waiting for manual review.

## Current Import Support

CSV import supports these optional columns:

- `has_diagram`
- `diagram_file_name`
- `diagram_url`
- `diagram_description`
- `needs_manual_review`

`diagram_url` creates a linked `QuestionMedia` row. CSV-only imports treat
`diagram_file_name` as a manual-review hint when no URL is provided.

ZIP imports can attach uploaded image files automatically. The ZIP must contain:

```text
questions.csv
diagrams/
  physics_2025_q1.png
  physics_2025_q2.jpg
  math_2024_q5.webp
```

`diagram_file_name` can be either a basename such as `physics_2025_q1.png` or a
path under `diagrams/`. If the basename is ambiguous, use the full `diagrams/...`
path.

Allowed image types are `.png`, `.jpg`, `.jpeg`, and `.webp`.

If a ZIP row references a missing image, the question is still imported as
`draft`, marked for manual review, and the import row receives a
`warning_message`. If both `diagram_url` and `diagram_file_name` are supplied,
the URL is used and the ZIP image is ignored with a warning.

Imported questions remain `draft` and must still be approved by a human before
assignments or practice can use them.

ZIP imports are parsed safely in memory. The backend does not extract archives
to disk and rejects unsafe paths such as `../evil.py`, absolute paths, encrypted
entries, unsupported file types, and unexpected files outside `questions.csv` or
`diagrams/`.

## API Exposure

Admin and teacher question-bank APIs include a `media` array on question
responses. Direct management endpoints are:

- `GET /api/question-bank/questions/{id}/media/`
- `POST /api/question-bank/questions/{id}/media/`
- `GET /api/question-bank/media/{id}/`
- `PATCH /api/question-bank/media/{id}/`
- `DELETE /api/question-bank/media/{id}/`

Students cannot manage or directly browse question-bank media. Student-facing
assignment/practice serializers should expose media only through safe attempt and
result payloads, without exposing correct answers before submission.

## Production Storage Note

Local media storage is acceptable only for short local testing. Render local
filesystem storage is not reliable for long-term uploaded media. Before serious
production use, move `QuestionMedia.image` storage to cloud media storage such
as S3-compatible storage or Cloudinary.

WhiteNoise serves static files, not durable user uploads.
