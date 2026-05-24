import { api } from "@/lib/api";
import type {
  AcademicSession,
  Assignment,
  AssignmentGeneratePayload,
  ClassArm,
  ClassLevel,
  LessonLog,
  LessonLogPayload,
  ListResponse,
  QueryParams,
  RegisterUserPayload,
  StudentEnrollment,
  Student,
  StudentProfile,
  StudentProfilePayload,
  Subject,
  TeacherAssignment,
  Teacher,
  TeacherProfile,
  TeacherProfilePayload,
  Term,
  Topic,
  User,
  UserListParams
} from "@/types/academics";

function unwrapList<T>(payload: T[] | ListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

function isListResponse<T>(payload: T[] | ListResponse<T>): payload is ListResponse<T> {
  return !Array.isArray(payload);
}

async function listResource<T>(path: string) {
  const payload = await api.get<T[] | ListResponse<T>>(path);
  return unwrapList(payload);
}

function queryString(params?: QueryParams) {
  if (!params) {
    return "";
  }

  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function listAllResource<T>(path: string, params?: QueryParams) {
  const pageSize = 100;
  const rows: T[] = [];
  let page = 1;

  while (true) {
    const payload = await api.get<T[] | ListResponse<T>>(
      `${path}${queryString({ ...params, page, page_size: pageSize })}`
    );

    if (!isListResponse(payload)) {
      return page === 1 ? payload : [...rows, ...payload];
    }

    rows.push(...payload.results);
    if (!payload.next || payload.results.length === 0 || rows.length >= payload.count) {
      return rows;
    }

    page += 1;
  }
}

export const getAcademicSessions = (params?: QueryParams) =>
  listResource<AcademicSession>(
    `/academics/academic-sessions/${queryString(params)}`
  );
export const createAcademicSession = (payload: Partial<AcademicSession>) =>
  api.post<AcademicSession>("/academics/academic-sessions/", payload);
export const updateAcademicSession = (
  id: number,
  payload: Partial<AcademicSession>
) => api.patch<AcademicSession>(`/academics/academic-sessions/${id}/`, payload);

export const getTerms = (params?: QueryParams) =>
  listResource<Term>(`/academics/terms/${queryString(params)}`);
export const createTerm = (payload: Partial<Term>) =>
  api.post<Term>("/academics/terms/", payload);
export const updateTerm = (id: number, payload: Partial<Term>) =>
  api.patch<Term>(`/academics/terms/${id}/`, payload);

export const getClassLevels = (params?: QueryParams) =>
  listResource<ClassLevel>(`/academics/class-levels/${queryString(params)}`);
export const getAllClassLevels = (params?: QueryParams) =>
  listAllResource<ClassLevel>("/academics/class-levels/", params);
export const createClassLevel = (payload: Partial<ClassLevel>) =>
  api.post<ClassLevel>("/academics/class-levels/", payload);
export const updateClassLevel = (id: number, payload: Partial<ClassLevel>) =>
  api.patch<ClassLevel>(`/academics/class-levels/${id}/`, payload);

export const getClassArms = (params?: QueryParams) =>
  listResource<ClassArm>(`/academics/class-arms/${queryString(params)}`);
export const createClassArm = (payload: Partial<ClassArm>) =>
  api.post<ClassArm>("/academics/class-arms/", payload);
export const updateClassArm = (id: number, payload: Partial<ClassArm>) =>
  api.patch<ClassArm>(`/academics/class-arms/${id}/`, payload);

export const getSubjects = (params?: QueryParams) =>
  listResource<Subject>(`/academics/subjects/${queryString(params)}`);
export const getAllSubjects = (params?: QueryParams) =>
  listAllResource<Subject>("/academics/subjects/", params);
export const createSubject = (payload: Partial<Subject>) =>
  api.post<Subject>("/academics/subjects/", payload);
export const updateSubject = (id: number, payload: Partial<Subject>) =>
  api.patch<Subject>(`/academics/subjects/${id}/`, payload);

export const getTopics = (params?: QueryParams) =>
  listResource<Topic>(`/academics/topics/${queryString(params)}`);
export const getAllTopics = (params?: QueryParams) =>
  listAllResource<Topic>("/academics/topics/", params);
export const createTopic = (payload: Partial<Topic>) =>
  api.post<Topic>("/academics/topics/", payload);
export const updateTopic = (id: number, payload: Partial<Topic>) =>
  api.patch<Topic>(`/academics/topics/${id}/`, payload);

export const getTeacherAssignments = (params?: QueryParams) =>
  listResource<TeacherAssignment>(
    `/academics/teacher-assignments/${queryString(params)}`
  );
export const createTeacherAssignment = (payload: Partial<TeacherAssignment>) =>
  api.post<TeacherAssignment>("/academics/teacher-assignments/", payload);
export const updateTeacherAssignment = (
  id: number,
  payload: Partial<TeacherAssignment>
) => api.patch<TeacherAssignment>(`/academics/teacher-assignments/${id}/`, payload);

export const getStudentEnrollments = (params?: QueryParams) =>
  listResource<StudentEnrollment>(
    `/academics/student-enrollments/${queryString(params)}`
  );
export const createStudentEnrollment = (payload: Partial<StudentEnrollment>) =>
  api.post<StudentEnrollment>("/academics/student-enrollments/", payload);
export const updateStudentEnrollment = (
  id: number,
  payload: Partial<StudentEnrollment>
) => api.patch<StudentEnrollment>(`/academics/student-enrollments/${id}/`, payload);

export const getLessonLogs = (params?: QueryParams) =>
  listResource<LessonLog>(`/academics/lesson-logs/${queryString(params)}`);
export const createLessonLog = (payload: LessonLogPayload) =>
  api.post<LessonLog>("/academics/lesson-logs/", payload);
export const getLessonLog = (id: number | string) =>
  api.get<LessonLog>(`/academics/lesson-logs/${id}/`);

export const getAssignments = (params?: QueryParams) =>
  listResource<Assignment>(`/assignments/${queryString(params)}`);
export const getAssignment = (id: number | string) =>
  api.get<Assignment>(`/assignments/${id}/`);
export const generateAssignmentFromTopic = (payload: AssignmentGeneratePayload) =>
  api.post<Assignment>("/assignments/generate-from-topic/", payload);
export const publishAssignment = (id: number | string) =>
  api.post<Assignment>(`/assignments/${id}/publish/`);
export const closeAssignment = (id: number | string) =>
  api.post<Assignment>(`/assignments/${id}/close/`);
export const archiveAssignment = (id: number | string) =>
  api.post<Assignment>(`/assignments/${id}/archive/`);

export const registerTeacher = (payload: RegisterUserPayload) =>
  api.post<User>("/auth/register/", payload);
export const registerStudent = (payload: RegisterUserPayload) =>
  api.post<User>("/auth/register/", payload);

export const getTeachers = (params?: UserListParams) =>
  listResource<Teacher>(`/auth/teachers/${queryString(params)}`);
export const getStudents = (params?: UserListParams) =>
  listResource<Student>(`/auth/students/${queryString(params)}`);

export const getTeacherProfiles = (params?: UserListParams) =>
  listResource<TeacherProfile>(`/auth/teacher-profiles/${queryString(params)}`);
export const createTeacherProfile = (payload: TeacherProfilePayload) =>
  api.post<TeacherProfile>("/auth/teacher-profiles/", payload);
export const updateTeacherProfile = (
  id: number,
  payload: Partial<TeacherProfilePayload>
) => api.patch<TeacherProfile>(`/auth/teacher-profiles/${id}/`, payload);

export const getStudentProfiles = (params?: UserListParams) =>
  listResource<StudentProfile>(`/auth/student-profiles/${queryString(params)}`);
export const createStudentProfile = (payload: StudentProfilePayload) =>
  api.post<StudentProfile>("/auth/student-profiles/", payload);
export const updateStudentProfile = (
  id: number,
  payload: Partial<StudentProfilePayload>
) => api.patch<StudentProfile>(`/auth/student-profiles/${id}/`, payload);
