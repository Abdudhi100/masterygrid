import { StudentProgressReport } from "@/components/analytics/StudentProgressReport";

export default function TeacherStudentProgressReportPage({
  params
}: {
  params: { id: string };
}) {
  return (
    <StudentProgressReport
      studentId={params.id}
      baseRole="teacher"
      backHref="/teacher/weak-students"
      backLabel="Back to Weak Students"
      printHref={`/teacher/students/${params.id}/progress-report/print`}
    />
  );
}
