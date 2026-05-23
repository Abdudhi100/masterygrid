import { Suspense } from "react";

import {
  AISuggestionDetailContent
} from "@/components/ai-generation/AISuggestionDetailContent";
import { LoadingState } from "@/components/ui/LoadingState";

export default function TeacherAISuggestionDetailPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading AI suggestion..." />}>
      <AISuggestionDetailContent
        id={params.id}
        basePath="/teacher/question-bank"
      />
    </Suspense>
  );
}
