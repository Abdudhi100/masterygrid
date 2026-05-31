import { StudentProgressReportPrint } from "@/components/analytics/StudentProgressReportPrint";

export default function AdminStudentProgressReportPrintPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <StudentProgressReportPrint
      studentId={params.id}
      backHref={`/admin/students/${params.id}/progress-report`}
    />
  );
}
