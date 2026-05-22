export type UserRole = "platform_admin" | "school_admin" | "teacher" | "student";

export type TeacherProfile = {
  id: number;
  user: number;
  user_email: string;
  user_full_name: string;
  school: number;
  staff_id: string;
  phone_number: string;
};

export type StudentProfile = {
  id: number;
  user: number;
  user_email: string;
  user_full_name: string;
  school: number;
  admission_number: string;
  guardian_name: string;
  guardian_phone: string;
};

export type CurrentUser = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  school: number | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  teacher_profile?: TeacherProfile | null;
  student_profile?: StudentProfile | null;
};

export type TokenPair = {
  access: string;
  refresh: string;
};

export type LoginCredentials = {
  email: string;
  password: string;
};
