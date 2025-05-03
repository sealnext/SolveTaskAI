export interface Thread {
  id: string;
  projectId: number;
  createdAt: string;
  updatedAt: string;
}

export class AgentClient {
  private baseUrl: string;
  private authToken: string;
  private abortController: AbortController | null = null;

  constructor(baseUrl: string, authToken: string) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  async getThreads(): Promise<Thread[]> {
    // Implementation
  }

  async deleteThread(threadId: string): Promise<boolean> {
    // Implementation
  }

  async sendMessage(options: {
    message: string;
    threadId?: string;
    projectId?: number;
    onProgress?: (content: string) => void;
    onComplete?: (threadId: string) => void;
    onInterrupt?: (data: { content: any; resumable: boolean }) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    // Implementation
  }

  async confirmAction(options: {
    threadId: string;
    payload?: Record<string, any>;
    ticket?: Record<string, any>;
    onProgress?: (content: string) => void;
    onComplete?: (threadId: string) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    // Implementation
  }

  async cancelAction(options: {
    threadId: string;
    onProgress?: (content: string) => void;
    onComplete?: (threadId: string) => void;
    onError?: (error: string) => void;
  }): Promise<{ threadId: string }> {
    // Implementation
  }

  abortCurrentStream(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}