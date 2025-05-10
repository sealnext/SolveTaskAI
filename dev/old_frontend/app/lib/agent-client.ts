export interface Thread {
  id: string;
  projectId: number;
  createdAt: string;
  updatedAt: string;
}

export class AgentClient {
  constructor(private baseUrl: string = '') {}

  private async request<T>(
    path: string, 
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any,
    callbacks?: {
      onComplete?: (data: T) => void;
      onError?: (error: string) => void;
    }
  ): Promise<T> {
    const options: RequestInit = {
      method,
      credentials: 'include'
    };

    if (body) {
      options.headers = {
        'Content-Type': 'application/json'
      };
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, options);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      
      if (callbacks?.onComplete) {
        callbacks.onComplete(data);
      }
      
      return data;
    } catch (error) {
      if (callbacks?.onError) {
        callbacks.onError(error.message);
      }
      throw error;
    }
  }

  async getThreads(): Promise<Thread[]> {
    return this.request<Thread[]>('/api/threads');
  }

  async deleteThread(threadId: string): Promise<boolean> {
    return this.request<boolean>(`/api/threads/${threadId}`, 'DELETE');
  }

  async sendMessage(options: {
    message: string;
    threadId?: string;
    projectId?: number;
    onComplete?: (threadId: string) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    return this.request<{ threadId: string }>(
      '/api/agent/message', 
      'POST',
      { 
        message: options.message, 
        threadId: options.threadId, 
        projectId: options.projectId 
      },
      {
        onComplete: options.onComplete ? 
          (data) => options.onComplete!(data.threadId) : undefined,
        onError: options.onError
      }
    );
  }

  async confirmAction(options: {
    threadId: string;
    payload?: Record<string, any>;
    ticket?: Record<string, any>;
    onComplete?: (threadId: string) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    return this.request<{ threadId: string }>(
      '/api/agent/confirm', 
      'POST',
      { 
        threadId: options.threadId, 
        payload: options.payload, 
        ticket: options.ticket 
      },
      {
        onComplete: options.onComplete ? 
          (data) => options.onComplete!(data.threadId) : undefined,
        onError: options.onError
      }
    );
  }

  async cancelAction(options: {
    threadId: string;
    onComplete?: (threadId: string) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    return this.request<{ threadId: string }>(
      '/api/agent/cancel', 
      'POST',
      { threadId: options.threadId },
      {
        onComplete: options.onComplete ? 
          (data) => options.onComplete!(data.threadId) : undefined,
        onError: options.onError
      }
    );
  }
}
