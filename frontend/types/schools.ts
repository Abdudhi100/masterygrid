export type SchoolSetupStepStatus = "complete" | "incomplete" | "warning";

export type SchoolSetupStep = {
  key: string;
  label: string;
  description: string;
  status: SchoolSetupStepStatus;
  count: number;
  required_count: number;
  action_url: string;
  recommendation: string;
};

export type SchoolSetupStatus = {
  school_id: number;
  school_name: string;
  completion_percentage: number;
  is_setup_complete: boolean;
  steps: SchoolSetupStep[];
  next_step: SchoolSetupStep | null;
  blocking_issues: string[];
  warnings: string[];
};
