import { PageHeader } from "@/components/layout/PageHeader";
import { AISuggestionHistory } from "@/components/ai-generation/AISuggestionHistory";

export default function TeacherAISuggestionsPage() {
  return (
    <>
      <PageHeader
        title="AI Suggestions"
        description="Review AI-assisted topic, difficulty, explanation, duplicate, and quality suggestions."
      />
      <AISuggestionHistory basePath="/teacher/question-bank" />
    </>
  );
}
