import { StudentProgressReport } from "@/components/analytics/StudentProgressReport";

export default function AdminStudentProgressReportPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <StudentProgressReport
      studentId={params.id}
      baseRole="admin"
      backHref="/admin/students"
      backLabel="Back to Students"
      printHref={`/admin/students/${params.id}/progress-report/print`}
    />
  );
}
