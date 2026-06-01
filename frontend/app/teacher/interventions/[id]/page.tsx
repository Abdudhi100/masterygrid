import { InterventionDetailPage } from "@/components/interventions/InterventionDetailPage";

export default function TeacherInterventionDetailRoute({
  params
}: {
  params: { id: string };
}) {
  return <InterventionDetailPage interventionId={params.id} baseRole="teacher" />;
}
