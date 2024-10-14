import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import ApiClient from "@/lib/apiClient";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Loader2, Plus, Trash2 } from 'lucide-react';
import SafeImage from '@/components/SafeImage';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast"

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
  isDeleted?: boolean;  // Adăugați această linie
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
  refreshInternalProjects: () => Promise<void>; // Adăugăm această nouă proprietate
}

const ApiKeyManager: React.FC<ApiKeyManagerProps> = ({ projects, onProjectsUpdate, onClose, refreshInternalProjects }) => {
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
  const [deletedProjects, setDeletedProjects] = useState<Set<string>>(new Set());
  const { toast } = useToast()

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

  const fetchExternalProjects = async (id?: number) => {
    const keyId = id || selectedApiKeyId;
    if (!keyId) return;

    setIsLoading(true);
    try {
      // Ensure we're passing a number, not an object
      const fetchedProjects = await apiClient.post<ExternalProjectSchema[]>(`/projects/external/id/${keyId}`);
      setExternalProjects(fetchedProjects);
      
      if (fetchedProjects.length > 0) {
        setMessage(`${fetchedProjects.length} external projects found.`);
      } else {
        setMessage('No external projects found.');
      }
    } catch (error) {
      console.error('Error fetching external projects:', error);
      if (error.message.includes('No projects found in external service')) {
        setMessage('No projects found in external service. Please check your API Key.');
      } else {
        setMessage(`Error fetching projects: ${error.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/api-keys/add', {
        service_type: serviceType,
        api_key: apiKey,
        domain,
        domain_email: email
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
      console.error('Error adding API key:', error);
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
        setMessage(error.message);
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

  const renderCompactApiKeyInfo = (key: ApiKey) => {
    return (
      <div className="flex items-center space-x-2 truncate">
        <Badge className={getServiceTypeColor(key.service_type)}>
          {key.service_type}
        </Badge>
        <span className="font-medium truncate">{formatDomain(key.domain)}</span>
      </div>
    );
  };

  const renderApiKeySelector = () => {
    const selectedKey = selectedApiKeyId 
      ? existingApiKeys.find(key => key.id === selectedApiKeyId) 
      : null;

    return (
      <Select 
        onValueChange={handleApiKeySelect} 
        value={selectedApiKeyId?.toString() || "default"}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select existing API Key">
            {selectedKey ? renderCompactApiKeyInfo(selectedKey) : "Select existing API Key"}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="default" disabled>Select existing API Key</SelectItem>
          {existingApiKeys.map(key => (
            <SelectItem key={key.id} value={key.id.toString()} className="py-2">
              <div className="flex flex-col space-y-1">
                {renderCompactApiKeyInfo(key)}
                <div className="text-sm text-muted-foreground">{key.domain_email}</div>
                <div className="text-xs text-muted-foreground">
                  {key.api_key.substring(0, 20)}...
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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
        key: project.key,
        api_key_id: selectedKey.id
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
      console.error('Error removing API key:', error);
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
        // Actualizează lista de proiecte externe
        setExternalProjects(prevProjects => 
          prevProjects.map(p => 
            p.id === project.id ? { ...p, isDeleted: true } : p
          )
        );
        
        // Apelăm funcția de reîmprospătare a proiectelor interne
        await refreshInternalProjects();
        
        toast({
          title: "Project Deleted",
          description: `Project "${project.name}" has been deleted successfully.`,
        });
      } else {
        setMessage(`Failed to delete project "${project.name}".`);
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      setMessage(`Error deleting project "${project.name}". Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  // Modifică renderizarea proiectelor pentru a include badge-ul "Deleted" și a simplifica butoanele
  const renderProjectItem = (project: ExternalProjectSchema) => {
    const isAdded = isProjectAlreadyAdded(project);
    const isNewlyAdded = newlyAddedProjects.has(project.id);
    return (
      <li 
        key={project.id} 
        className={`flex items-center justify-between p-2 rounded-md ${
          isAdded || isNewlyAdded || project.isDeleted ? 'bg-muted' : 'bg-card'
        }`}
      >
        <div className="flex items-center space-x-2">
          <SafeImage 
            src={project.avatarUrl} 
            alt={project.name} 
            width={24}
            height={24} 
            className="w-6 h-6 rounded" 
          />
          <span>{project.name}</span>
          <span className="text-sm text-muted-foreground">({project.key})</span>
        </div>
        {project.isDeleted ? (
          <Badge variant="destructive">Deleted</Badge>
        ) : isNewlyAdded ? (
          <Badge variant="secondary">Added</Badge>
        ) : isAdded ? (
          <div className="flex space-x-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleReloadEmbeddings(project)}
                    disabled={isLoading}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Reload Embeddings</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <AlertDialog>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertDialogTrigger asChild>
                      <Button size="icon" variant="ghost">
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </AlertDialogTrigger>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Delete Project</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete the project
                    and remove all associated data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => handleDeleteProject(project)}>
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        ) : (
          <Button
            size="sm"
            onClick={() => handleAddInternalProject(project)}
            disabled={isLoading}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add
          </Button>
        )}
      </li>
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
            <div className="mt-4 flex items-center space-x-4">
              <div className="flex-grow">
                {renderApiKeySelector()}
              </div>
              <div className="flex space-x-2">
                {selectedApiKeyId && (
                  <>
                    <Button
                      onClick={() => fetchExternalProjects(selectedApiKeyId)}
                      disabled={isLoading}
                      className="p-2 rounded-full hover:bg-accent transition-colors duration-200"
                      variant="ghost"
                      size="icon"
                    >
                      <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          className="p-2 rounded-full hover:bg-destructive/90 transition-colors duration-200"
                          variant="destructive"
                          size="icon"
                        >
                          <Trash2 className="w-5 h-5" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the API key
                            and remove its data from our servers.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => selectedApiKeyId && handleRemoveApiKey(selectedApiKeyId)}
                            className="text-destructive-foreground hover:bg-primaryAccent"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </>
                )}
              </div>
            </div>
          )}

          {apiKeySource === 'new' && (
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="serviceType" className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Project Management Platform <span className="text-destructive">*</span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">Choose the platform you use for project tracking and documentation</p>
                <Select 
                  onValueChange={(value) => setServiceType(value as 'jira' | 'azure')} 
                  id="serviceType"
                  required
                >
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
                  API Token / Personal Access Token <span className="text-destructive">*</span>
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
                  Organization URL <span className="text-destructive">*</span>
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
                  Account Email <span className="text-destructive">*</span>
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
            <Button type="submit" disabled={isLoading || !serviceType || !apiKey || !domain || !email}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Add API Key
            </Button>
          )}
        </form>
        {message && (
          <p className={`mt-4 text-sm ${message.includes('Error') ? 'text-destructive' : 'text-foreground'}`}>
            {message}
          </p>
        )}
        {externalProjects.length > 0 && apiKeySource === 'existing' && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold mb-2">External Projects:</h3>
            <ScrollArea className="h-[200px]">
              <ul className="space-y-2">
                {externalProjects.map(renderProjectItem)}
              </ul>
            </ScrollArea>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeyManager;