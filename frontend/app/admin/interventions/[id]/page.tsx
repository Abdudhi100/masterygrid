import { InterventionDetailPage } from "@/components/interventions/InterventionDetailPage";

export default function AdminInterventionDetailRoute({
  params
}: {
  params: { id: string };
}) {
  return <InterventionDetailPage interventionId={params.id} baseRole="admin" />;
}
