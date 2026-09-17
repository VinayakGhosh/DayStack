// API utility module for handling all requests

// An empty value supports same-site deployments; local development supplies it
// through VITE_API_BASE_URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

interface ApiResponse<T> {
  data?: T;
  error?: string;
  errorCode?: string;
}

const csrfToken = (): string | undefined =>
  document.cookie.split('; ').find((entry) => entry.startsWith('daystack_csrf='))?.split('=')[1];
const handleResponse = async <T>(response: Response): Promise<ApiResponse<T>> => {
  if (response.status === 204) {
    return { data: undefined as T };
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const detail = errorData.detail;
    return {
      error: typeof detail === 'string' ? detail : detail?.message || 'An error occurred',
      errorCode: typeof detail === 'object' ? detail?.code : undefined,
    };
  }

  const data = await response.json();
  return { data };
};

const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const token = csrfToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'X-CSRF-Token': token }),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });
    return handleResponse<T>(response);
  } catch (error) {
    return { error: 'Network error. Please check your connection.' };
  }
};

// Auth endpoints
export const authApi = {
  login: (email: string, password: string) =>
    apiRequest<Member>(
      "/v1/sessions/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    ),

  register: (data: { display_name: string; email: string; password: string; time_zone: string }) =>
    apiRequest<Member>('/v1/sessions/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  refresh: () => apiRequest<Member>('/v1/sessions/refresh', { method: 'POST' }),

  logout: () => apiRequest<void>('/v1/sessions/logout', { method: 'POST' }),

  getProfile: () => apiRequest<Member>('/v1/sessions/current-member'),

  updateProfile: (data: Partial<Member>) =>
    apiRequest<Member>('/v1/sessions/current-member', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  updatePassword: (data: { current_password: string; new_password: string }) =>
    apiRequest<void>('/v1/sessions/password', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

// Projects endpoints
export const projectsApi = {
  getAll: () => apiRequest<Project[]>('/v1/project/'),

  getById: (id: string) => apiRequest<Project>(`/v1/project/${id}`),

  getUsage: () => apiRequest<ProjectQuota>('/v1/project/usage'),

  create: (data: { name: string; description?: string }) =>
    apiRequest<Project>('/v1/project/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: { name?: string; description?: string }) =>
    apiRequest<Project>(`/v1/project/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiRequest<void>(`/v1/project/${id}`, {
      method: 'DELETE',
    }),
};

// Project Status endpoints
export const projectStatusApi = {
  getAll: (projectId: string) =>
    apiRequest<ProjectStatus[]>(`/v1/project/${projectId}/statuses`),

  create: (projectId: string, data: { name: string; description?: string }) =>
    apiRequest<ProjectStatus>(`/v1/project/${projectId}/statuses`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (projectId: string, statusId: string, data: { name?: string; description?: string; is_completion?: boolean }) =>
    apiRequest<ProjectStatus>(`/v1/project/${projectId}/statuses/${statusId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  reorder: (projectId: string, statusIds: string[]) =>
    apiRequest<ProjectStatus[]>(`/v1/project/${projectId}/statuses/reorder`, {
      method: 'PUT',
      body: JSON.stringify({ status_ids: statusIds }),
    }),

  delete: (projectId: string, statusId: string, reassignToStatusId?: string) =>
    apiRequest<void>(`/v1/project/${projectId}/statuses/${statusId}`, {
      method: 'DELETE',
      ...(reassignToStatusId && { body: JSON.stringify({ reassign_to_status_id: reassignToStatusId }) }),
    }),
};

// Tasks endpoints
export const tasksApi = {
  getByProject: (projectId: string) =>
    apiRequest<Task[]>(`/v1/tasks/?project_id=${projectId}`),

  create: (data: TaskInput & { project_id: string }) =>
    apiRequest<Task>('/v1/tasks/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<TaskInput>) =>
    apiRequest<Task>(`/v1/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  moveStatus: (id: string, status_id: string) =>
    apiRequest<Task>(`/v1/tasks/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ status_id }),
    }),

  delete: (id: string) =>
    apiRequest<void>(`/v1/tasks/${id}`, {
      method: 'DELETE',
    }),

  getUsage: (projectId: string) => apiRequest<TaskQuota>(`/v1/tasks/project/${projectId}/usage`),

  setSubtasks: (taskId: string, subtasks: SubtaskInput[]) =>
    apiRequest<Task>(`/v1/tasks/${taskId}/subtasks`, { method: 'PUT', body: JSON.stringify(subtasks) }),

  toggleSubtask: (taskId: string, subtaskId: string, is_completed: boolean) =>
    apiRequest<Subtask>(`/v1/tasks/${taskId}/subtasks/${subtaskId}`, {
      method: 'PATCH', body: JSON.stringify({ is_completed }),
    }),
};

export const labelsApi = {
  getAll: () => apiRequest<Label[]>('/v1/tasks/labels/'),
  create: (data: { name: string; color?: string }) => apiRequest<Label>('/v1/tasks/labels/', {
    method: 'POST', body: JSON.stringify(data),
  }),
  update: (id: string, data: { name?: string; color?: string }) => apiRequest<Label>(`/v1/tasks/labels/${id}`, {
    method: 'PATCH', body: JSON.stringify(data),
  }),
  delete: (id: string) => apiRequest<void>(`/v1/tasks/labels/${id}`, { method: 'DELETE' }),
};

// Subscription endpoints
export const subscriptionApi = {
  getCurrent: () => apiRequest<Subscription>('/v1/subscription/current'),

  getPlans: () => apiRequest<Plan[]>('/v1/plans/'),

  getUsage: () => apiRequest<Usage>('/v1/stats/'),

  upgrade: (planId: string) =>
    apiRequest<Subscription>(`/v1/subscription/${planId}`, {
      method: 'POST',
    }),
};

// Types
export interface Member {
  member_id: string;
  email: string;
  display_name: string;
  time_zone: string;
}

export interface Project {
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  total_tasks: number;
  completed_tasks: number;
}

export interface ProjectStatus {
  status_id: string;
  project_id: string;
  name: string;
  description?: string;
  is_completion: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectQuota {
  used: number;
  limit: number;
  remaining: number;
}

export interface Task {
  task_id: string;
  project_id: string;
  name: string;
  description?: string | null;
  due_date?: string | null;
  priority: Priority;
  labels: Label[];
  subtasks: Subtask[];
  status_id: string | null;
  status_name?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type Priority = 'none' | 'low' | 'medium' | 'high';

export interface Label {
  label_id: string;
  name: string;
  color?: string | null;
}

export interface Subtask {
  subtask_id: string;
  text: string;
  display_order: number;
  is_completed: boolean;
}

export interface SubtaskInput {
  text: string;
  is_completed: boolean;
}

export interface TaskInput {
  name: string;
  description?: string | null;
  due_date?: string | null;
  priority: Priority;
  label_ids?: string[];
  subtasks?: SubtaskInput[];
}

export interface TaskQuota {
  used: number;
  limit: number;
  remaining: number;
}

export interface Subscription {
  id: string;
  plan_id: string;
  plan_name: string;
  status: 'active' | 'cancelled' | 'expired' | 'Active' | 'Cancelled' | 'Expired';
  current_period_start: string;
  current_period_end: string;
  features: string[];
  max_projects: number;
  task_per_day: number;
  export_allowed: boolean;
}

export interface Plan {
  plan_id: string;
  plan_tier: string;
  price: number;
  duration_days: number;
  max_projects: number;
  task_per_day: number;
  export_allowed: boolean;
}

export interface Usage {
  projects_count: number;
  tasks_count: number;
  tasks_completed_count: number;
  tasks_in_progress_count: number;
  tasks_pending_count: number;
  task_limit: number;
  project_limit: number;
}
