const cacheManager = {
  cache: new Map<string, {data: any, timestamp: number}>(),

  CACHE_DURATION: 5 * 60 * 1000,

  get(key: string) {
    const cached = this.cache.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > this.CACHE_DURATION) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  },

  set(key: string, data: any) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
};

interface RequestOptions extends RequestInit {
  cacheKey?: string;
}

export default function ApiClient() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const refreshToken = async () => {
    console.log("------ Refreshing token automatically");
    const response = await fetch(`${baseUrl}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }
  };

  const request = async (endpoint: string, options: RequestOptions = {}, retryCount = 0) => {
    const { cacheKey, ...fetchOptions } = options;

    if (cacheKey) {
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return { data: cachedData, status: 200 };
      }
    }

    try {
      const url = new URL(endpoint, baseUrl);
      const response = await fetch(url, {
        ...fetchOptions,
        credentials: 'include',
      });

      if (response.status === 401 && retryCount < 1) {
        await refreshToken();
        return request(endpoint, options, retryCount + 1);
      }

      if (!response.ok) {
        if (response.status === 204) {
          return { status: response.status };
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || errorData.detail || `API call failed: ${response.statusText}`);
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1 && response.status !== 204) {
        const data = await response.json();
        if (cacheKey) {
          cacheManager.set(cacheKey, data);
        }
        return { data, status: response.status };
      } else {
        return { status: response.status };
      }
    } catch (error) {
      console.error("Request error:", error);
      throw error;
    }
  };

  const get = async (endpoint: string, options: RequestOptions = {}) => {
    return request(endpoint, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  };

  const post = async (endpoint: string, data: any) => {
    return request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  };

  const remove = async (endpoint: string) => {
    return request(endpoint, {
      method: 'DELETE',
    });
  };

  const getIssueStatuses = async (projectId: string) => {
    const cacheKey = `statuses-${projectId}`;
    const response = await get(`/ticketing/${projectId}/statuses`, { cacheKey });
    return response.data;
  };

  return { post, get, remove, getIssueStatuses };
}
