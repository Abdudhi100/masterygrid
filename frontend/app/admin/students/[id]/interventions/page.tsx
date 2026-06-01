import { StudentInterventionsPage } from "@/components/interventions/StudentInterventionsPage";

export default function AdminStudentInterventionsRoute({
  params
}: {
  params: { id: string };
}) {
  return <StudentInterventionsPage studentId={params.id} baseRole="admin" />;
}
