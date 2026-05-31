import type { APIRequestContext } from "@playwright/test";

import {
  buildAcademicSessionData,
  buildApprovedQuestionData,
  buildClassArmData,
  buildClassLevelData,
  buildQuestionSourceData,
  buildStudentData,
  buildSubjectData,
  buildTeacherData,
  buildTermData,
  buildTopicData,
  uniqueRunId
} from "../fixtures/testData";
import {
  apiGet,
  apiPost,
  E2EApiError,
  loginApi,
  type TokenPair
} from "./api";
import {
  assertProductionAllowedForMutatingTests,
  backendApiUrl,
  credentials
} from "./env";

type CurrentUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  school: number | null;
};

type CreatedRecord = {
  id: number;
  [key: string]: unknown;
};

type SeedCredentials = {
  email: string;
  password: string;
};

export type SeedPracticeWorkflowData = {
  runId: string;
  adminToken: string;
  admin: CurrentUser;
  teacherCredentials: SeedCredentials;
  studentCredentials: SeedCredentials;
  ids: {
    school: number;
    academicSession: number;
    term: number;
    classLevel: number;
    classArm: number;
    subject: number;
    topic: number;
    teacher: number;
    student: number;
    teacherAssignment: number;
    studentEnrollment: number;
    questionSource: number | null;
    questions: number[];
    assignment: number;
  };
  names: {
    subject: string;
    topic: string;
    classLevel: string;
    classArm: string;
  };
};

async function createEntity<T extends CreatedRecord>(
  request: APIRequestContext,
  token: string,
  path: string,
  data: unknown,
  label: string
) {
  try {
    return await apiPost<T>(request, path, token, data);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(
      `Failed to create ${label}. Payload: ${JSON.stringify(data)}. ${message}`
    );
  }
}

function requireSchoolId(admin: CurrentUser) {
  if (admin.school) {
    return admin.school;
  }

  throw new Error(
    "E2E API seed requires admin credentials for a school-scoped user. " +
      "This backend does not expose a school creation API, so a platform_admin " +
      "without a school cannot prepare seeded workflow data. Use a school_admin " +
      "account or seed a demo school first."
  );
}

function adminSeedLoginError(error: unknown) {
  const originalMessage = error instanceof Error ? error.message : String(error);
  const passwordSet = process.env.E2E_ADMIN_PASSWORD ? "yes" : "no";

  return new Error(
    [
      "E2E seed setup could not log in with the configured admin credentials.",
      `E2E_BACKEND_API_URL: ${backendApiUrl}`,
      `E2E_ADMIN_EMAIL: ${credentials.admin.email}`,
      `E2E_ADMIN_PASSWORD set: ${passwordSet}`,
      "Password value is intentionally not printed.",
      "",
      "If you are using local demo credentials, seed the backend first:",
      "  cd backend",
      "  .\\venv\\Scripts\\python.exe manage.py seed_demo_data --with-submissions",
      "",
      "Also confirm the frontend E2E env points at the backend/database that contains that admin account.",
      `Original login error: ${originalMessage}`
    ].join("\n")
  );
}

export async function seedPracticeWorkflowData(
  request: APIRequestContext
): Promise<SeedPracticeWorkflowData> {
  assertProductionAllowedForMutatingTests();

  const runId = uniqueRunId();
  console.log(`[e2e] seed runId=${runId}`);
  let tokenPair: TokenPair;
  try {
    tokenPair = await loginApi(
      request,
      credentials.admin.email,
      credentials.admin.password
    );
  } catch (error) {
    throw adminSeedLoginError(error);
  }
  const adminToken = tokenPair.access;
  const admin = await apiGet<CurrentUser>(request, "auth/me/", adminToken);
  const schoolId = requireSchoolId(admin);

  const sessionPayload = {
    ...buildAcademicSessionData(runId),
    school: schoolId
  };
  const academicSession = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/academic-sessions/",
    sessionPayload,
    "academic session"
  );

  const termPayload = {
    ...buildTermData(runId, academicSession.id),
    school: schoolId
  };
  const term = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/terms/",
    termPayload,
    "term"
  );

  const classLevelPayload = {
    ...buildClassLevelData(runId),
    school: schoolId
  };
  const classLevel = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/class-levels/",
    classLevelPayload,
    "class level"
  );

  const classArmPayload = {
    ...buildClassArmData(runId, classLevel.id),
    school: schoolId
  };
  const classArm = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/class-arms/",
    classArmPayload,
    "class arm"
  );

  const subjectPayload = {
    ...buildSubjectData(runId),
    school: schoolId
  };
  const subject = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/subjects/",
    subjectPayload,
    "subject"
  );

  const topicPayload = {
    ...buildTopicData(runId, subject.id, classLevel.id),
    school: schoolId
  };
  const topic = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/topics/",
    topicPayload,
    "topic"
  );

  const teacherPayload = buildTeacherData(runId, schoolId);
  const teacher = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "auth/register/",
    teacherPayload,
    "teacher user"
  );

  const studentPayload = buildStudentData(runId, schoolId);
  const student = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "auth/register/",
    studentPayload,
    "student user"
  );

  const teacherAssignment = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/teacher-assignments/",
    {
      school: schoolId,
      teacher: teacher.id,
      class_arm: classArm.id,
      subject: subject.id,
      academic_session: academicSession.id,
      term: term.id,
      is_active: true
    },
    "teacher class subject assignment"
  );

  const studentEnrollment = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "academics/student-enrollments/",
    {
      school: schoolId,
      student: student.id,
      class_arm: classArm.id,
      academic_session: academicSession.id,
      term: term.id,
      is_active: true
    },
    "student enrollment"
  );

  let questionSource: CreatedRecord | null = null;
  try {
    questionSource = await apiPost<CreatedRecord>(
      request,
      "question-bank/sources/",
      adminToken,
      buildQuestionSourceData(runId),
    );
  } catch (error) {
    if (!(error instanceof E2EApiError) || error.status !== 403) {
      throw error;
    }
  }

  const approvedQuestionIds: number[] = [];
  for (let index = 1; index <= 5; index += 1) {
    const question = await createEntity<CreatedRecord>(
      request,
      adminToken,
      "question-bank/questions/",
      {
        ...buildApprovedQuestionData(
          runId,
          subject.id,
          classLevel.id,
          topic.id,
          questionSource?.id ?? null,
          index
        ),
        school: schoolId
      },
      `question ${index}`
    );

    const approvedQuestion = await apiPost<CreatedRecord>(
      request,
      `question-bank/questions/${question.id}/approve/`,
      adminToken,
      {}
    );
    approvedQuestionIds.push(approvedQuestion.id);
  }

  const assignment = await createEntity<CreatedRecord>(
    request,
    adminToken,
    "assignments/generate-from-topic/",
    {
      teacher: teacher.id,
      class_arm: classArm.id,
      subject: subject.id,
      topic: topic.id,
      title: `E2E Practice Assignment ${runId}`,
      instructions: "Generated by E2E setup.",
      question_count: 5,
      duration_minutes: 30,
      due_at: "2026-12-31T23:59:00Z"
    },
    "teacher assignment"
  );

  const publishedAssignment = await apiPost<CreatedRecord>(
    request,
    `assignments/${assignment.id}/publish/`,
    adminToken,
    {}
  );

  return {
    runId,
    adminToken,
    admin,
    teacherCredentials: {
      email: teacherPayload.email,
      password: teacherPayload.password
    },
    studentCredentials: {
      email: studentPayload.email,
      password: studentPayload.password
    },
    ids: {
      school: schoolId,
      academicSession: academicSession.id,
      term: term.id,
      classLevel: classLevel.id,
      classArm: classArm.id,
      subject: subject.id,
      topic: topic.id,
      teacher: teacher.id,
      student: student.id,
      teacherAssignment: teacherAssignment.id,
      studentEnrollment: studentEnrollment.id,
      questionSource: questionSource?.id ?? null,
      questions: approvedQuestionIds,
      assignment: publishedAssignment.id
    },
    names: {
      subject: String(subjectPayload.name),
      topic: String(topicPayload.title),
      classLevel: String(classLevelPayload.name),
      classArm: `${classLevelPayload.name} ${classArmPayload.name}`
    }
  };
}
