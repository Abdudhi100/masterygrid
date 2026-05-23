import { Suspense } from "react";

import {
  AISuggestionDetailContent
} from "@/components/ai-generation/AISuggestionDetailContent";
import { LoadingState } from "@/components/ui/LoadingState";

export default function AdminAISuggestionDetailPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<LoadingState label="Loading AI suggestion..." />}>
      <AISuggestionDetailContent
        id={params.id}
        basePath="/admin/question-bank"
      />
    </Suspense>
  );
}
