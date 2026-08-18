export interface AppInfo {
  bundle_id: string;
  name: string;
  developer: string;
  category: string;
  icon_url: string;
  price: string;
  rating: number;
  review_count: number;
}

export interface ValidateLinkResponse {
  valid: boolean;
  bundle_id?: string;
  app_info?: AppInfo;
  error?: string;
}

export interface ValidateLinkRequest {
  url: string;
}

export interface CreateTaskRequest {
  bundle_id: string;
  url: string;
  app_info: AppInfo;
  user_goal: string;
  filters: any;
}

export interface CreateTaskResponse {
  task_id: string;
  status: string;
}

export interface ProgressStage {
  name: string;
  name_cn: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  timestamp?: string;
}

export interface Progress {
  task_id: string;
  progress_percent: number;
  current_stage: string;
  stages: ProgressStage[];
  status?: string;
}

export interface Category {
  name: string;
  description?: string;
  review_ids: string[];
  sentiment?: 'positive' | 'negative' | 'neutral' | 'mixed';
  key_points?: string[];
}

export interface Finding {
  id?: number;
  title: string;
  description: string;
  evidence_strength: 'strong' | 'medium' | 'weak';
  supporting_review_ids: string[];
  representative_quotes?: string[];
  suggested_action?: string;
  is_positive?: boolean;
  is_hypothesis?: boolean;
  is_contradictory?: boolean;
  data_limitation?: string;
}

export interface Requirement {
  id: string;
  finding_id?: number;
  title: string;
  user_story: string;
  priority: 'P0' | 'P1' | 'P2';
  version_suggestion: 'V1' | 'V2';
}

export interface TestCase {
  id?: number;
  requirement_id: string;
  title: string;
  preconditions?: string;
  given: string;
  when: string;
  then: string;
  type: 'positive' | 'negative';
}

export interface VerificationIssue {
  severity: 'high' | 'medium' | 'low';
  finding_id?: number;
  requirement_id?: string;
  message: string;
}

export interface Verification {
  passed: string[];
  issues: VerificationIssue[];
  overall_status: 'pass' | 'fail';
  summary: string;
}

export interface Deliverables {
  goal_analysis?: { focus_areas: string[]; analysis_intents: string[]; suggested_filters: any };
  categories?: Category[];
  findings?: Finding[];
  prd?: { requirements: Requirement[]; version_plan: any };
  test_cases?: TestCase[];
  verification?: Verification;
  cleaning_report?: any;
  app_info?: AppInfo;
}

export interface TaskResults {
  task_id: string;
  status: 'completed' | 'failed' | 'running';
  app_info?: AppInfo;
  goal_analysis?: { focus_areas: string[]; analysis_intents: string[]; suggested_filters: any };
  categories?: Category[];
  findings?: Finding[];
  prd?: { requirements: Requirement[]; version_plan: any };
  test_cases?: TestCase[];
  verification?: Verification;
  cleaned_reviews?: any[];
  is_fallback?: boolean;
  data_source?: string;
  cleaning_report?: any;
  error?: string;
  // 原始 API 响应中的嵌套字段
  deliverables?: Deliverables;
  progress_percent?: number;
  current_stage?: string;
  message?: string;
}
