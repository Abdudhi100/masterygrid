import { StudentInterventionsPage } from "@/components/interventions/StudentInterventionsPage";

export default function TeacherStudentInterventionsRoute({
  params
}: {
  params: { id: string };
}) {
  return <StudentInterventionsPage studentId={params.id} baseRole="teacher" />;
}
