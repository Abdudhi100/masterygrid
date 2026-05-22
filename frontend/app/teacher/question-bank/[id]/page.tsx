import { Suspense } from "react";

import { QuestionDetailContent } from "@/components/question-bank/QuestionDetailContent";
import { LoadingState } from "@/components/ui/LoadingState";

export default function TeacherQuestionDetailPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading question..." />}>
      <QuestionDetailContent
        id={params.id}
        mode="teacher"
        basePath="/teacher/question-bank"
      />
    </Suspense>
  );
}
