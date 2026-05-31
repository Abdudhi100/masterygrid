import { StudentProgressReportPrint } from "@/components/analytics/StudentProgressReportPrint";

export default function TeacherStudentProgressReportPrintPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <StudentProgressReportPrint
      studentId={params.id}
      backHref={`/teacher/students/${params.id}/progress-report`}
    />
  );
}
