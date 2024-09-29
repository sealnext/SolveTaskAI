import { getAuthTokens } from './auth';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const { accessToken, csrfToken } = getAuthTokens();
    const headers = new Headers(options.headers || {});
    
    if (accessToken) headers.append('Authorization', `Bearer ${accessToken}`);
    if (csrfToken) headers.append('X-CSRF-Token', csrfToken);

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      // Handle errors, possibly refresh token if 401
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return response.json();
  }

  async get(endpoint: string) {
    return this.request(endpoint);
  }

  async post(endpoint: string, data: any) {
    return this.request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  }

  // Add other methods like put, delete, etc.
}

// Create and export an instance
export const apiClient = new ApiClient('http://localhost:8000');