import { testPassword } from "../utils/env";

export function uniqueRunId() {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).slice(2, 7);
  return `${timestamp}${random}`.slice(0, 14);
}

export function buildTeacherData(runId: string, schoolId: number) {
  return {
    email: `e2e.teacher.${runId}@masterygrid.test`,
    full_name: `E2E Teacher ${runId}`,
    password: testPassword,
    role: "teacher",
    school: schoolId,
    staff_id: `E2E-T-${runId}`,
    phone_number: "08000000001"
  };
}

export function buildStudentData(runId: string, schoolId: number) {
  return {
    email: `e2e.student.${runId}@masterygrid.test`,
    full_name: `E2E Student ${runId}`,
    password: testPassword,
    role: "student",
    school: schoolId,
    admission_number: `E2E-S-${runId}`,
    guardian_name: `E2E Guardian ${runId}`,
    guardian_phone: "08000000002"
  };
}

export function buildAcademicSessionData(runId: string) {
  return {
    name: `E2E ${runId}`,
    starts_at: "2026-01-01",
    ends_at: "2026-12-31",
    is_active: false
  };
}

export function buildTermData(runId: string, sessionId: number) {
  return {
    academic_session: sessionId,
    name: "first",
    starts_at: "2026-01-01",
    ends_at: "2026-04-30",
    is_active: false
  };
}

export function buildClassLevelData(runId: string) {
  return {
    name: `E2E SS2 ${runId}`,
    description: `E2E class level for ${runId}`,
    is_active: true
  };
}

export function buildClassArmData(runId: string, classLevelId: number) {
  return {
    class_level: classLevelId,
    name: `Science ${runId}`,
    description: `E2E class arm for ${runId}`,
    is_active: true
  };
}

export function buildSubjectData(runId: string) {
  return {
    name: `E2E Physics ${runId}`,
    code: `E2E-${runId}`.slice(0, 32),
    description: `E2E subject for ${runId}`,
    is_jamb_subject: true,
    is_active: true
  };
}

export function buildTopicData(
  runId: string,
  subjectId: number,
  classLevelId: number
) {
  return {
    subject: subjectId,
    class_level: classLevelId,
    title: `E2E Motion ${runId}`,
    description: `E2E topic for ${runId}`,
    curriculum_tags: ["e2e", runId],
    jamb_relevance_level: "high",
    is_active: true
  };
}

export function buildQuestionSourceData(runId: string) {
  return {
    name: `E2E JAMB Source ${runId}`,
    source_type: "jamb_past_question",
    exam_body: "JAMB",
    year: 2026,
    description: `E2E question source for ${runId}`,
    is_active: true
  };
}

export function buildApprovedQuestionData(
  runId: string,
  subjectId: number,
  classLevelId: number,
  topicId: number,
  sourceId: number | null,
  index: number
) {
  const correctLabel = ["A", "B", "C", "D"][index % 4];

  return {
    subject: subjectId,
    class_level: classLevelId,
    topic: topicId,
    source: sourceId,
    question_text: `E2E ${runId} question ${index}: Which option best describes a basic motion fact?`,
    explanation: `E2E explanation ${index} for ${runId}.`,
    difficulty: index % 3 === 0 ? "hard" : index % 2 === 0 ? "medium" : "easy",
    status: "draft",
    is_active: true,
    options: ["A", "B", "C", "D"].map((label) => ({
      label,
      text: `E2E option ${label} for ${runId} question ${index}`,
      is_correct: label === correctLabel
    }))
  };
}
