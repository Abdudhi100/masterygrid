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

`diagram_url` creates a linked `QuestionMedia` row. `diagram_file_name` is stored
in import row raw data and marks the question for manual review when no URL is
provided. ZIP/image file matching is not implemented yet.

Imported questions remain `draft` and must still be approved by a human before
assignments or practice can use them.

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
