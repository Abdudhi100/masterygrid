import { api } from "@/lib/api";
import type {
  StudentAnswerInput,
  StudentAssignmentItem,
  Submission,
  SubmissionResult,
  SubmissionStart
} from "@/types/submissions";

export const getMyAssignments = () =>
  api.get<StudentAssignmentItem[]>("/submissions/my-assignments/");

export const startAssignment = (assignmentId: number | string) =>
  api.post<SubmissionStart>("/submissions/start-assignment/", {
    assignment: Number(assignmentId)
  });

export const getSubmission = (submissionId: number | string) =>
  api.get<Submission>(`/submissions/${submissionId}/`);

export const submitAssignment = (
  submissionId: number | string,
  answers: StudentAnswerInput[]
) =>
  api.post<SubmissionResult>(`/submissions/${submissionId}/submit/`, {
    answers
  });

export const getSubmissionResult = (submissionId: number | string) =>
  api.get<SubmissionResult>(`/submissions/${submissionId}/result/`);
