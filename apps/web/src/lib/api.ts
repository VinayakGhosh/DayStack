// API utility module for handling all requests

// const API_BASE_URL = import.meta.env.VITE_API_URL
// const API_BASE_URL = "http://65.2.144.240/api/";
const API_BASE_URL = "http://localhost:8000";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}
interface UserLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
  user_id: string;
  refresh_token_expires_at: string;
}

const getToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

export const setToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

export const clearToken = (): void => {
  localStorage.removeItem('auth_token');
};

export const isAuthenticated = (): boolean => {
  return !!getToken();
};

const handleResponse = async <T>(response: Response): Promise<ApiResponse<T>> => {
  if (response.status === 401) {
    if (window.location.pathname !== '/login') {
      clearToken();
      window.location.href = '/login';
      return { error: 'Session expired. Please login again.' };
    }
    // If on login page, let the standard error handling deal with it
  }

  if (response.status === 204) {
    return { data: undefined as T };
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { error: errorData.detail || 'An error occurred' };
  }

  const data = await response.json();
  return { data };
};

const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
    return handleResponse<T>(response);
  } catch (error) {
    return { error: 'Network error. Please check your connection.' };
  }
};

// Auth endpoints
export const authApi = {
  login: (email: string, password: string) =>
    apiRequest<UserLoginResponse>(
      "/v1/users/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      }
    ),

  register: (data: { first_name: string; last_name: string; email: string; password: string }) =>
    apiRequest<{ message: string }>('/v1/users/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getProfile: () => apiRequest<User>('/v1/users/me'),

  updateProfile: (data: Partial<User>) =>
    apiRequest<User>('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  updatePassword: (data: { current_password: string; new_password: string }) =>
    apiRequest<{ message: string }>('/auth/password', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

// Projects endpoints
export const projectsApi = {
  getAll: () => apiRequest<Project[]>('/v1/project/'),

  getById: (id: string) => apiRequest<Project>(`/v1/project/?project_id=${id}`),

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

  update: (projectId: string, statusId: string, data: { name?: string; description?: string }) =>
    apiRequest<ProjectStatus>(`/v1/project/${projectId}/statuses/${statusId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (projectId: string, statusId: string) =>
    apiRequest<void>(`/v1/project/${projectId}/statuses/${statusId}`, {
      method: 'DELETE',
    }),
};

// Tasks endpoints
export const tasksApi = {
  getByProject: (projectId: string) =>
    apiRequest<Task[]>(`/v1/tasks/?project_id=${projectId}`),

  create: (data: { project_id: string; name: string; description?: string }) =>
    apiRequest<Task>('/v1/tasks/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: { name?: string; description?: string }) =>
    apiRequest<Task>(`/v1/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  moveStatus: (id: string, status_id: string) =>
    apiRequest<{ task_id: string; status_id: string; status_name: string }>(`/v1/tasks/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ status_id }),
    }),

  delete: (id: string) =>
    apiRequest<void>(`/v1/tasks/${id}`, {
      method: 'DELETE',
    }),
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
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
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
  created_at: string;
  updated_at: string;
}

export interface Task {
  task_id: string;
  project_id: string;
  name: string;
  description?: string;
  status_id: string | null;
  status_name?: string | null;
  created_by: string;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
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
