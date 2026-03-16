export interface LoginPayload {
  username: string;
  password: string;
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  version: string;
  created_at: string;
}

export interface DashboardSummary {
  project_count: number;
  wire_count: number;
  parallel_group_count: number;
  annotation_count: number;
}

export interface DistributionItem {
  name: string;
  value: number;
}

export interface ParallelGroup {
  id: number;
  project_id: number;
  group_name: string;
  count: number;
  total_area: number;
  start_terminal: string;
  end_terminal: string;
  parallel_type: string;
  suggestion: string;
  created_at: string;
}

export interface Annotation {
  id: number;
  group_id: number;
  text: string;
  position_x: number;
  position_y: number;
  style: string;
  created_at: string;
}

export interface ImportRecord {
  id: number;
  project_id: number;
  filename: string;
  file_format: string;
  row_count: number;
  status: string;
  created_at: string;
}

export interface OperationLog {
  id: number;
  user_id: number | null;
  action: string;
  target: string;
  detail: string;
  created_at: string;
}
