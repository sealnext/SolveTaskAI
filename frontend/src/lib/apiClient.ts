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

  const request = async (endpoint: string, options: RequestInit = {}, retryCount = 0) => {
    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        ...options,
        credentials: 'include',
      });

      if (response.status === 401 && retryCount < 1) {
        // Încearcă să reînnoiești token-ul și să reîncerci cererea
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
        return { data, status: response.status };
      } else {
        return { status: response.status };
      }
    } catch (error) {
      console.error("Request error:", error);
      throw error;
    }
  };

  const get = async (endpoint: string) => {
    return request(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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

  return { post, get, remove };
}
