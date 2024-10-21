import { ApiKey } from './types';
import React from 'react';
import { Badge } from '@/components/ui/badge';

export const getServiceTypeColor = (serviceType: string) => {
  switch (serviceType.toLowerCase()) {
    case 'azure':
      return 'bg-primary text-primary-foreground';
    case 'jira':
      return 'bg-secondary text-secondary-foreground';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export const formatDomain = (domain?: string) => {
  if (!domain) return '';
  return domain.replace(/^https?:\/\//, '').replace(/\/$/, '').split('/')[0];
};

export const renderCompactApiKeyInfo = (key: ApiKey) => {
  return (
    <div className="flex items-center space-x-2 truncate">
      <Badge className={getServiceTypeColor(key.service_type)}>
        {key.service_type}
      </Badge>
      <span className="font-medium truncate">{formatDomain(key.domain)}</span>
    </div>
  );
};