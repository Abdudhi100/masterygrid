"use client";

import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/layout/PageHeader";
import { QuestionForm } from "@/components/question-bank/QuestionForm";
import { createQuestion } from "@/lib/questionBank";

export default function TeacherNewQuestionPage() {
  const router = useRouter();

  return (
    <>
      <PageHeader
        title="Create Question"
        description="Create a draft school question for admin review."
      />
      <QuestionForm
        submitLabel="Create Draft Question"
        cancelHref="/teacher/question-bank"
        onSubmit={createQuestion}
        onSaved={(question) => router.push(`/teacher/question-bank/${question.id}`)}
      />
    </>
  );
}
