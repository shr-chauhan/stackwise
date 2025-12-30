/**
 * API client for backend integration
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Token storage key
const API_TOKEN_KEY = 'debug_ai_api_token';

export interface ApiError {
  detail: string;
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

/**
 * Get API token from localStorage (client-side) or return null (server-side)
 */
export function getApiToken(): string | null {
  if (typeof window === 'undefined') {
    return null; // Server-side
  }
  return localStorage.getItem(API_TOKEN_KEY);
}

/**
 * Set API token in localStorage
 */
export function setApiToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(API_TOKEN_KEY, token);
  }
}

/**
 * Remove API token from localStorage
 */
export function clearApiToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(API_TOKEN_KEY);
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  requireAuth: boolean = true
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log('apiRequest called:', endpoint, 'requireAuth:', requireAuth);
  
  // Get auth token if required
  const token = requireAuth ? getApiToken() : null;
  console.log('Token found:', !!token);
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add Authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  console.log('Making fetch request to:', url);
  
  // Create AbortController for timeout (10 seconds)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    
    console.log('Fetch response received:', response.status, response.statusText);
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      let errorDetail: string;
      try {
        const errorData = await response.json() as ApiError;
        errorDetail = errorData.detail || response.statusText;
      } catch {
        errorDetail = response.statusText;
      }
      
      console.error(`API request failed: ${response.status} ${response.statusText}`, {
        url,
        status: response.status,
        detail: errorDetail
      });
      
      throw new ApiClientError(
        `API request failed: ${errorDetail}`,
        response.status,
        errorDetail
      );
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json() as Promise<T>;
    }
    
    return {} as T;
  } catch (error) {
    clearTimeout(timeoutId);
    
    // Handle timeout/abort errors
    if (error instanceof Error && (error.name === 'AbortError' || error.message.includes('aborted'))) {
      throw new ApiClientError(
        'Request timeout: Backend server did not respond in time. Please ensure the backend is running.',
        408,
        'Request timeout'
      );
    }
    
    // Re-throw other errors (including ApiClientError)
    throw error;
  }
}

// Project types
export interface Project {
  id: number;
  project_key: string;
  name: string;
  repo_config: {
    provider?: string;
    owner?: string;
    repo?: string;
    branch?: string;
  } | null;
  created_at: string;
  error_count?: number;
}

export interface ProjectCreate {
  name: string;
  project_key: string;
  repo_provider?: string;
  repo_owner?: string;
  repo_name?: string;
  branch?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

// Error event types
export interface ErrorEvent {
  id: number;
  timestamp: string;
  status_code: number | null;
  message: string;
  method: string;
  path: string;
  project_key: string;
  project_name: string;
  created_at: string;
  has_analysis: boolean;
}

export interface ErrorEventListResponse {
  events: ErrorEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface ErrorEventDetail {
  id: number;
  timestamp: string;
  status_code: number | null;
  payload: {
    message: string;
    stack?: string;
    method: string;
    path: string;
  };
  created_at: string;
  project: {
    id: number;
    project_key: string;
    name: string;
  };
}

export interface ErrorAnalysis {
  id: number;
  error_event_id: number;
  analysis_text: string;
  model: string;
  confidence: string | null;
  created_at: string;
}

export interface ErrorEventWithAnalysis {
  event: ErrorEventDetail;
  analysis: ErrorAnalysis | null;
}

// User types
export interface User {
  id: number;
  github_id: string;
  username: string;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  api_token: string;
  created_at: string;
}

export interface UserSyncRequest {
  github_id: string;
  username: string;
  email?: string | null;
  name?: string | null;
  avatar_url?: string | null;
}

// API functions
export const api = {
  // Authentication
  async syncUser(userData: UserSyncRequest): Promise<User> {
    const user = await apiRequest<User>('/api/v1/auth/sync-user', {
      method: 'POST',
      body: JSON.stringify(userData),
    }, false); // Don't require auth for user sync
    
    // Store API token
    setApiToken(user.api_token);
    
    return user;
  },

  // Projects
  // Projects
  async getProjects(): Promise<ProjectListResponse> {
    return apiRequest<ProjectListResponse>('/api/v1/projects');
  },

  async getProject(projectId: number): Promise<Project> {
    return apiRequest<Project>(`/api/v1/projects/${projectId}`);
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    return apiRequest<Project>('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Error events
  async getErrorEvents(params?: {
    project_key?: string;
    limit?: number;
    offset?: number;
  }): Promise<ErrorEventListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.project_key) searchParams.set('project_key', params.project_key);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const query = searchParams.toString();
    return apiRequest<ErrorEventListResponse>(
      `/api/v1/events${query ? `?${query}` : ''}`
    );
  },

  async getErrorEvent(eventId: number): Promise<ErrorEventDetail> {
    return apiRequest<ErrorEventDetail>(`/api/v1/events/${eventId}`);
  },

  async getErrorEventWithAnalysis(eventId: number): Promise<ErrorEventWithAnalysis> {
    return apiRequest<ErrorEventWithAnalysis>(`/api/v1/events/${eventId}/with-analysis`);
  },
};

