import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from 'lucide-react';

interface NewApiKeyFormProps {
  onSubmit: (formData: {
    serviceType: 'jira' | 'azure',
    apiKey: string,
    domain: string,
    email: string
  }) => Promise<void>;
  isLoading: boolean;
}

const NewApiKeyForm: React.FC<NewApiKeyFormProps> = ({ onSubmit, isLoading }) => {
  const [serviceType, setServiceType] = useState<'jira' | 'azure'>('jira');
  const [apiKey, setApiKey] = useState('');
  const [domain, setDomain] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ serviceType, apiKey, domain, email });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-6">
            <div className="space-y-2">
            <label htmlFor="serviceType" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mt-4">
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
      <Button type="submit" disabled={isLoading || !serviceType || !apiKey || !domain || !email}>
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
        Add API Key
      </Button>
    </form>
    );
};

export default NewApiKeyForm;