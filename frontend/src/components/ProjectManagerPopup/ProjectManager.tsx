import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import ApiClient from "@/lib/apiClient";
import { Loader2 } from 'lucide-react';
import { useToast } from "@/hooks/use-toast"
import { ApiKeyManagerProps, ApiKey, ExternalProjectSchema, Project } from '@/lib/types';
import NewApiKeyForm from './NewApiKeyForm';
import ExistingApiKeySelector from './ExistingApiKeySelector';
import ExternalProjectsList from './ExternalProjectsList';

const ApiKeyManager: React.FC<ApiKeyManagerProps> = ({ projects, onProjectsUpdate, onClose, refreshInternalProjects }) => {
  const [apiKeySource, setApiKeySource] = useState<'new' | 'existing'>('new');
  const [existingApiKeys, setExistingApiKeys] = useState<ApiKey[]>([]);
  const [selectedApiKeyId, setSelectedApiKeyId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [externalProjects, setExternalProjects] = useState<ExternalProjectSchema[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [newlyAddedProjects, setNewlyAddedProjects] = useState<Set<string>>(new Set());
  const { toast } = useToast()
  const [apiKey, setApiKey] = useState('');
  const [domain, setDomain] = useState('');
  const [email, setEmail] = useState('');
  const [serviceType, setServiceType] = useState<'jira' | 'azure'>('jira');

  const apiClient = ApiClient();

  useEffect(() => {
    fetchExistingApiKeys();
  }, []);

  const fetchExistingApiKeys = async () => {
    setIsInitialLoading(true);
    try {
      const response = await apiClient.get('/api-keys');
      const keys: ApiKey[] = response.data.data;
      setExistingApiKeys(keys);
      if (keys.length > 0) {
        setApiKeySource('existing');
      }
    } catch (error) {
      console.error('Error fetching API keys:', error);
    } finally {
      setIsInitialLoading(false);
    }
  };

  const fetchExternalProjects = async (id?: number) => {
    const keyId = id || selectedApiKeyId;
    if (!keyId) return;

    setIsLoading(true);
    try {
      const fetchedProjects = await apiClient.post<ExternalProjectSchema[]>(`/projects/external/id/${keyId}`);
      setExternalProjects(fetchedProjects.data);
      
      if (fetchedProjects.data.length > 0) {
        setMessage(`${fetchedProjects.data.length} external projects found.`);
      } else {
        setMessage('No external projects found.');
        setExternalProjects([]);
      }
    } catch (error) {
      setExternalProjects([]); 
      if (error.response && error.response.status === 404) {
        setMessage('No projects found in external service. Please check your API Key.');
      } else {
        setMessage(error.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData: {
    serviceType: 'jira' | 'azure',
    apiKey: string,
    domain: string,
    email: string
  }) => {
    setMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/api-keys/add', {
        service_type: formData.serviceType,
        api_key: formData.apiKey,
        domain: formData.domain,
        domain_email: formData.email
      });
      
      if (response.data && response.data.id) {
        setMessage('API Key added successfully!');
        await fetchExistingApiKeys();
        setApiKeySource('existing');
        setSelectedApiKeyId(response.data.id);
        // Automatically fetch external projects after adding the key
        await fetchExternalProjects(response.data.id);
      } else {
        setMessage('API Key added, but no ID was returned. Please try refreshing.');
      }
    } catch (error) {
      if (error.response && error.response.data && error.response.data.message) {
        setMessage(`Error: ${error.response.data.message}`);
      } else {
        setMessage(`Error adding API key: ${error.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiKeySelect = async (keyId: string) => {
    const id = parseInt(keyId);
    setSelectedApiKeyId(id);
    setIsLoading(true);
    setExternalProjects([]); // Golim lista de proiecte externe înainte de a încărca altele noi
    
    const selectedKey = existingApiKeys.find(key => key.id === id);
    if (selectedKey) {
      setServiceType(selectedKey.service_type as 'jira' | 'azure');
      setDomain(selectedKey.domain);
      setEmail(selectedKey.domain_email);
      
      await fetchExternalProjects(id);
    }
  };

  const handleApiKeySourceChange = (value: 'new' | 'existing') => {
    setApiKeySource(value);
    if (value === 'new') {
      // Clear external projects, related data, and messages when switching to 'Add New API Key'
      setExternalProjects([]);
      setMessage('');
      setSelectedApiKeyId(null);
      // Reset other form fields
      setApiKey('');
      setDomain('');
      setEmail('');
    }
  };

  const handleAddInternalProject = async (project: ExternalProjectSchema) => {
    if (!selectedApiKeyId) return;

    const selectedKey = existingApiKeys.find(key => key.id === selectedApiKeyId);
    if (!selectedKey) return;

    setIsLoading(true);
    try {
      const newProjectData = {
        name: project.name,
        domain: selectedKey.domain,
        service_type: selectedKey.service_type,
        internal_id: project.id,
        key: project.key,
        api_key_id: selectedKey.id
      };

      const response = await apiClient.post('/projects/internal/add', newProjectData);

      if (response.status === 200) {
        const newProject: Project = {
          ...newProjectData,
          id: response.data.project_id
        };
        onProjectsUpdate([...projects, newProject]);
        setMessage(response.data.message);
        setNewlyAddedProjects(prev => new Set(prev).add(project.id));
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReloadEmbeddings = async (project: ExternalProjectSchema) => {
    setIsLoading(true);
    try {
      await apiClient.post('/projects/reload-embeddings', { projectKey: project.key });
      setMessage(`Embeddings reloaded for project "${project.name}"`);
    } catch (error) {
      setMessage(`Error reloading embeddings for "${project.name}". Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveApiKey = async (keyId: number) => {
    setIsLoading(true);
    try {
      await apiClient.remove(`/api-keys/${keyId}`);
      setExistingApiKeys(prevKeys => prevKeys.filter(key => key.id !== keyId));
      setMessage('API Key removed successfully.');
      setSelectedApiKeyId(null);
      setExternalProjects([]);
      onProjectsUpdate(projects.filter(project => project.id !== keyId));
    } catch (error) {
      setMessage(`Error removing API key: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteProject = async (project: ExternalProjectSchema) => {
    setIsLoading(true);
    try {
      const response = await apiClient.remove(`/projects/internal/${project.id}`);
      if (response.status === 204) {
        setMessage(`Project "${project.name}" deleted successfully.`);
        setExternalProjects(prevProjects => 
          prevProjects.map(p => 
            p.id === project.id ? { ...p, isDeleted: true } : p
          )
        );
        
        await refreshInternalProjects();
        
        toast({
          title: "Project Deleted",
          description: `Project "${project.name}" has been deleted successfully.`,
        });
      } else {
        setMessage(`Failed to delete project "${project.name}".`);
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitialLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
        <div className="bg-background p-6 rounded-2xl shadow-xl max-w-md w-full flex flex-col items-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="mt-2 text-sm text-muted-foreground">Loading API Keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-background p-6 rounded-2xl shadow-xl max-w-md w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Project Manager</h2>
          <button 
            onClick={onClose} 
            className="text-gray-500 hover:text-gray-700 transition-colors duration-200"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {existingApiKeys.length > 0 && (
          <Select onValueChange={handleApiKeySourceChange} defaultValue={apiKeySource}>
            <SelectTrigger>
              <SelectValue placeholder="Choose API Key Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="new">Add New API Key</SelectItem>
              <SelectItem value="existing">Use Existing API Key</SelectItem>
            </SelectContent>
          </Select>
        )}

        {apiKeySource === 'existing' && existingApiKeys.length > 0 && (
          <ExistingApiKeySelector
            existingApiKeys={existingApiKeys}
            selectedApiKeyId={selectedApiKeyId}
            onApiKeySelect={handleApiKeySelect}
            onRemoveApiKey={handleRemoveApiKey}
          />
        )}

        {apiKeySource === 'new' && (
          <NewApiKeyForm onSubmit={handleSubmit} isLoading={isLoading} />
        )}

        {message && (
          <p className={`mt-4 text-sm ${message.includes('Error') ? 'text-destructive' : 'text-foreground'}`}>
            {message}
          </p>
        )}

        {externalProjects.length > 0 && apiKeySource === 'existing' && (
          <ExternalProjectsList
            externalProjects={externalProjects}
            projects={projects}
            isLoading={isLoading}
            newlyAddedProjects={newlyAddedProjects}
            onAddInternalProject={handleAddInternalProject}
            onReloadEmbeddings={handleReloadEmbeddings}
            onDeleteProject={handleDeleteProject}
          />
        )}
      </div>
    </div>
  );
};

export default ApiKeyManager;
