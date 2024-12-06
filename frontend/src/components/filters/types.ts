import { LucideIcon } from 'lucide-react';

export interface Filter {
  id: string;
  label: string;
  icon: LucideIcon;
  count?: number;
  options?: string[];
  isMulti?: boolean;
}

export interface FilterGroup {
  group: string;
  items: Filter[];
}

export interface BaseFilterCommandProps {
  projectId: number;
  activeFilters: Filter[];
  onActiveFiltersChange: (filters: Filter[]) => void;
  onBack: () => void;
} 