export interface ApiKey {
    id: number;
    api_key: string;
    created_at: Date | null;
    domain: string;
    domain_email: string;
    expires_at: Date | null;
    permissions: string | null;
    service_type: string;
  }
  
  export interface ExternalProjectSchema {
    name: string;
    key: string;
    id: string;
    avatarUrl: string;
    project_type_key: string;
    style: string;
    isDeleted?: boolean;
  }
  
  export interface Project {
    id: number;
    name: string;
    key: string;
    domain: string;
    service_type: string;
  }
  
  export interface ApiKeyManagerProps {
    projects: Project[];
    onProjectsUpdate: (newProjects: Project[]) => void;
    onClose: () => void;
    refreshInternalProjects: () => Promise<void>;
  }