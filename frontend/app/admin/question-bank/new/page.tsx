"use client";

import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/layout/PageHeader";
import { QuestionForm } from "@/components/question-bank/QuestionForm";
import { createQuestion } from "@/lib/questionBank";

export default function AdminNewQuestionPage() {
  const router = useRouter();

  return (
    <>
      <PageHeader
        title="Create Question"
        description="Create a school-specific objective question with four options."
      />
      <QuestionForm
        submitLabel="Create Question"
        cancelHref="/admin/question-bank"
        onSubmit={createQuestion}
        onSaved={(question) => router.push(`/admin/question-bank/${question.id}`)}
      />
    </>
  );
}
