import { Suspense } from "react";

import { QuestionDetailContent } from "@/components/question-bank/QuestionDetailContent";
import { LoadingState } from "@/components/ui/LoadingState";

export default function AdminQuestionDetailPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading question..." />}>
      <QuestionDetailContent
        id={params.id}
        mode="admin"
        basePath="/admin/question-bank"
      />
    </Suspense>
  );
}
