export default function ApiClient() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  /*
  This function when called will return a response object with the following properties:
  - data: the data returned from the API call
  - status: the status code of the response
  */

  const request = async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 204) {
        return { status: response.status };
      }
      const errorData = await response.json().catch(() => ({}));
      console.error("API Error:", response.status, errorData);
      throw new Error(errorData.message || errorData.detail || `API call failed: ${response.statusText}`);
    }

    // Verifică dacă răspunsul are conținut înainte de a încerca să-l parseze ca JSON
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1 && response.status !== 204) {
      const data = await response.json();
      return { data, status: response.status };
    } else {
      return { status: response.status };
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
