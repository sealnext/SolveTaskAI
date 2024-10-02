import { log } from "console";
import { useSession } from "next-auth/react";


export default function ApiClient() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;

  const { data: session } = useSession();

  const request = async (endpoint: string, options: RequestInit = {}) => {
    const csrfToken = session?.user?.csrf_token;
    
    const headers = new Headers(options.headers || {});
    if (csrfToken) headers.append('X-CSRF-Token', csrfToken);

    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return response.json();
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

  return { post };
}

