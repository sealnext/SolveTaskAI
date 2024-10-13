import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import ApiClient from "@/lib/apiClient";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Loader2, Plus } from 'lucide-react';

interface ApiKey {
  id: number;
  api_key: string;
  created_at: Date | null;
  domain: string;
  domain_email: string;
  expires_at: Date | null;
  permissions: string | null;
  service_type: string;
}

interface ExternalProjectSchema {
  name: string;
  key: string;
  id: string;
  avatarUrl: string;
  project_type_key: string;
  style: string;
}

interface Project {
  id: number;
  name: string;
  key: string;
  domain: string;
  service_type: string;
}

interface ApiKeyManagerProps {
  projects: Project[];
  onProjectsUpdate: (newProjects: Project[]) => void;
  onClose: () => void;
}

const ApiKeyManager: React.FC<ApiKeyManagerProps> = ({ projects, onProjectsUpdate, onClose }) => {
  const [apiKeySource, setApiKeySource] = useState<'new' | 'existing'>('new');
  const [serviceType, setServiceType] = useState<'jira' | 'azure'>('jira');
  const [apiKey, setApiKey] = useState('');
  const [domain, setDomain] = useState('');
  const [email, setEmail] = useState('');
  const [existingApiKeys, setExistingApiKeys] = useState<ApiKey[]>([]);
  const [selectedApiKeyId, setSelectedApiKeyId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [externalProjects, setExternalProjects] = useState<ExternalProjectSchema[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [newlyAddedProjects, setNewlyAddedProjects] = useState<Set<string>>(new Set());

  const apiClient = ApiClient();

  useEffect(() => {
    fetchExistingApiKeys();
  }, []);

  const fetchExistingApiKeys = async () => {
    setIsInitialLoading(true);
    try {
      const response = await apiClient.get('/api-keys');
      const keys: ApiKey[] = response.data;
    
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');

    if (serviceType === 'jira') {
      try {
        const response = await apiClient.post('/projects/external', {
          service_type: serviceType,
          api_key: apiKey,
          domain,
          domain_email: email
        });

        const newProjects = response.filter((newProject: Project) => 
          !projects.some(existingProject => existingProject.key === newProject.key)
        );

        if (newProjects.length > 0) {
          onProjectsUpdate([...projects, ...newProjects]);
          setMessage('New projects added successfully!');
        } else {
          setMessage('All projects are already added.');
        }
      } catch (error) {
        console.error('Error adding projects:', error);
        setMessage('Error adding projects. Please try again.');
      }
    } else {
      setMessage('Azure integration is not implemented yet.');
    }
  };

  const fetchExternalProjects = async () => {
    if (!selectedApiKeyId) return;

    setIsLoading(true);
    try {
      const fetchedProjects = await apiClient.post<ExternalProjectSchema[]>(`/projects/external/id/${selectedApiKeyId}`);
      setExternalProjects(fetchedProjects);
      
      if (fetchedProjects.length > 0) {
        setMessage(`${fetchedProjects.length} external projects found.`);
      } else {
        setMessage('No external projects found.');
      }
    } catch (error) {
      console.error('Error fetching external projects:', error);
      setMessage('Error fetching external projects. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiKeySelect = async (keyId: string) => {
    const id = parseInt(keyId);
    setSelectedApiKeyId(id);
    setIsLoading(true);
    
    const selectedKey = existingApiKeys.find(key => key.id === id);
    if (selectedKey) {
      setServiceType(selectedKey.service_type as 'jira' | 'azure');
      setDomain(selectedKey.domain);
      setEmail(selectedKey.domain_email);
      
      try {
        const fetchedProjects = await apiClient.post<ExternalProjectSchema[]>(`/projects/external/id/${id}`);
        setExternalProjects(fetchedProjects);
        
        if (fetchedProjects.length > 0) {
          setMessage(`${fetchedProjects.length} external projects found.`);
        } else {
          setMessage('No external projects found.');
        }
      } catch (error) {
        console.error('Error fetching external projects:', error);
        setMessage('Error fetching external projects. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const getServiceTypeColor = (serviceType: string) => {
    switch (serviceType.toLowerCase()) {
      case 'jira':
        return 'bg-primary text-primary-foreground';
      case 'azure':
        return 'bg-secondary text-secondary-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const formatDomain = (domain?: string) => {
    if (!domain) return '';
    return domain.replace(/^https?:\/\//, '').replace(/\/$/, '').split('/')[0];
  };

  const renderApiKeySelector = () => {
    return (
      <Select onValueChange={handleApiKeySelect} value={selectedApiKeyId?.toString()}>
        <SelectTrigger>
          <SelectValue placeholder="Select existing API Key">
            {selectedApiKeyId !== null && renderSelectedApiKey()}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {existingApiKeys.map(key => (
            <SelectItem key={key.id} value={key.id.toString()} className="py-2">
              <div className="flex flex-col space-y-1">
                <div className="flex items-center space-x-2">
                  <Badge className={getServiceTypeColor(key.service_type)}>
                    {key.service_type}
                  </Badge>
                  <span className="font-medium text-foreground">{formatDomain(key.domain)}</span>
                </div>
                <div className="text-sm text-muted-foreground">{key.domain_email}</div>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="text-xs text-muted-foreground truncate w-48 cursor-pointer">
                        {key.api_key.substring(0, 20)}...
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs">{key.api_key}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  };

  const renderSelectedApiKey = () => {
    if (selectedApiKeyId === null) return null;
    const selectedKey = existingApiKeys.find(key => key.id === selectedApiKeyId);
    if (!selectedKey) return null;

    return (
      <div className="flex items-center space-x-2">
        <Badge className={getServiceTypeColor(selectedKey.service_type)}>
          {selectedKey.service_type}
        </Badge>
        <span className="font-medium">{formatDomain(selectedKey.domain)}</span>
      </div>
    );
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
      const response = await apiClient.post('/projects/internal/add', {
        name: project.name,
        domain: selectedKey.domain,
        service_type: selectedKey.service_type,
        internal_id: project.id,
        key: project.key
      });

      if (response && response.id) {
        const newProject: Project = {
          id: response.id,
          name: response.name,
          key: response.key,
          domain: response.domain,
          service_type: response.service_type
        };
        onProjectsUpdate([...projects, newProject]);
        setMessage(`Project "${project.name}" added successfully!`);
        setNewlyAddedProjects(prev => new Set(prev).add(project.id));
      } else {
        setMessage(`Failed to add project "${project.name}". ${response.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error adding internal project:', error);
      setMessage(`Error adding project "${project.name}". Please try again.`);
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
      console.error('Error reloading embeddings:', error);
      setMessage(`Error reloading embeddings for "${project.name}". Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  const isProjectAlreadyAdded = (externalProject: ExternalProjectSchema) => {
    return projects.some(internalProject => 
      internalProject.key === externalProject.key || 
      internalProject.name === externalProject.name
    );
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
          <h2 className="text-lg font-semibold">API Key Manager</h2>
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
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <div className="mt-4 flex justify-between items-center">
              {renderApiKeySelector()}
              {selectedApiKeyId && (
                <Button
                  onClick={fetchExternalProjects}
                  disabled={isLoading}
                  className="ml-2 p-2 rounded-full hover:bg-accent transition-colors duration-200"
                  variant="ghost"
                  size="icon"
                >
                  <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
                </Button>
              )}
            </div>
          )}

          {apiKeySource === 'new' && (
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="serviceType" className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Project Management Platform
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">Choose the platform you use for project tracking and documentation</p>
                <Select onValueChange={(value) => setServiceType(value as 'jira' | 'azure')} id="serviceType">
                  <SelectTrigger>
                    <SelectValue placeholder="Select your platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="jira">Jira (Atlassian)</SelectItem>
                    <SelectItem value="azure">Azure DevOps (Microsoft)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label htmlFor="apiKey" className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  API Token / Personal Access Token
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">Your secure key to access the platform's API (found in your account settings)</p>
                <Input
                  id="apiKey"
                  type="text"
                  placeholder="e.g., ATAtt3xFx1...K9_1e8mXNBpxatqBFxt1"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="domain" className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Organization URL
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">The web address of your organization's project management space</p>
                <Input
                  id="domain"
                  type="url"
                  placeholder="e.g., https://your-company.atlassian.net"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Account Email
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">The email address associated with your platform account</p>
                <Input
                  id="email"
                  type="email"
                  placeholder="e.g., john.doe@your-company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
          )}
          {apiKeySource === 'new' && (
            <Button type="submit">
              Add API Key
            </Button>
          )}
        </form>
        {message && apiKeySource === 'existing' && (
          <p className="mt-4 text-sm text-foreground">{message}</p>
        )}
        {externalProjects.length > 0 && apiKeySource === 'existing' && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold mb-2">External Projects:</h3>
            <ScrollArea className="h-[200px]">
              <ul className="space-y-2">
                {externalProjects.map(project => {
                  const isAdded = isProjectAlreadyAdded(project);
                  const isNewlyAdded = newlyAddedProjects.has(project.id);
                  return (
                    <li 
                      key={project.id} 
                      className={`flex items-center justify-between p-2 rounded-md ${isAdded || isNewlyAdded ? 'bg-muted' : 'bg-card'}`}
                    >
                      <div className="flex items-center space-x-2">
                        <div className="flex-shrink-0">
                          <img 
                            src={project.avatarUrl} 
                            alt={project.name} 
                            className="w-8 h-8 rounded-full"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = '/default-avatar.png';
                            }}
                          />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium">{project.name}</span>
                          <span className="text-sm text-muted-foreground">{project.key}</span>
                        </div>
                      </div>
                      {isNewlyAdded ? (
                        <Button
                          disabled
                          size="sm"
                          className="bg-muted text-muted-foreground"
                        >
                          Added
                        </Button>
                      ) : isAdded ? (
                        <Button
                          onClick={() => handleReloadEmbeddings(project)}
                          size="sm"
                          className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <RefreshCw className="w-4 h-4 mr-1" />
                              Reload
                            </>
                          )}
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleAddInternalProject(project)}
                          size="sm"
                          className="bg-primary text-primary-foreground hover:bg-primary/90"
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <Plus className="w-4 h-4 mr-1" />
                              Add Project
                            </>
                          )}
                        </Button>
                      )}
                    </li>
                  );
                })}
              </ul>
            </ScrollArea>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeyManager;