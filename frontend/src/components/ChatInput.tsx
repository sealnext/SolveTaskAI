import React, { useState, useRef, KeyboardEvent, useEffect } from 'react';
import ProjectSelector from './ProjectSelector';
import { Project } from '@/types/project';
import { useSearchParams } from 'next/navigation';
import { FilterCommand } from "@/components/FilterCommand"
import { Badge } from "./ui/badge"
import { X, ChevronRight } from "lucide-react"
import { Button } from "./ui/button"
import { Filter } from "./filters/types"

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onAddNewProject: () => void;
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isLoading,
  projects,
  selectedProjectId,
  onSelectProject,
  onAddNewProject 
}) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const searchParams = useSearchParams();
  const chatId = searchParams.get('chat_id');
  const MAX_CHARS = 3000;
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Filter[]>([]);
  const filtersContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButtons, setShowScrollButtons] = useState(false);
  const isDesktop = useMediaQuery('(min-width: 768px)');
  const visibleFilters = isDesktop ? 3 : 1;

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFilterClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFilterOpen(!isFilterOpen)
  }

  const removeFilter = (filterId: string) => {
    setActiveFilters(activeFilters.filter(f => f.id !== filterId))
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit}>
        <div className="bg-backgroundSecondary bg-opacity-80 backdrop-filter backdrop-blur-md rounded-2xl shadow-lg border-2 border-muted overflow-hidden">
          {/* Main input container */}
          <div className="px-4 py-3 flex items-center justify-between">
            {/* Input field */}
            <div className="flex-grow flex items-center min-w-0">
              <div className="w-full relative">
                {/* Input pentru desktop */}
                <input
                  ref={inputRef}
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message here..."
                  className="hidden md:block bg-transparent border-none focus:outline-none w-full h-full text-sm text-foreground placeholder-foreground-secondary"
                  disabled={isLoading}
                  maxLength={MAX_CHARS}
                />
                
                {/* Input pentru mobile */}
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedProjectId ? `Send a message in ${projects.find(p => p.id === selectedProjectId)?.name}...` : 'Select a project...'}
                  className="md:hidden bg-transparent border-none focus:outline-none w-full h-full text-sm text-foreground placeholder-foreground-secondary"
                  disabled={isLoading}
                  maxLength={MAX_CHARS}
                />
              </div>
            </div>

            {/* Send button and Project Selector container */}
            <div className="flex items-center gap-2 ml-2">
              {/* Send button */}
              <div className="flex-shrink-0">
                <button
                  type="submit"
                  disabled={isLoading || !message.trim()}
                className={`
                    gooey-button bg-primary text-foreground rounded-full
                    focus:outline-none p-1.5 relative overflow-hidden
                    ${isLoading || !message.trim()
                      ? 'hidden md:block md:opacity-0 md:transition-all md:duration-300'
                      : 'hover:bg-primaryAccent'
                    }
                  `}
                >
                  {isLoading ? (
                    <svg className="animate-spin h-4 w-4 text-foreground" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 transition-all duration-1000" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Project Selector */}
              {!chatId && (
                <div className={`flex-shrink-0 ${message.trim() ? 'md:block hidden' : 'block'}`}>
                  <ProjectSelector
                    projects={projects}
                    selectedProjectId={selectedProjectId}
                    onSelectProject={onSelectProject}
                    onAddNewProject={onAddNewProject}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Separator line */}
          <div className="h-px bg-muted/30"></div>

          {/* Bottom toolbar */}
          <div className="px-4 py-2 bg-black/5 dark:bg-white/5 flex justify-between items-center">
            {/* Left side - Filters */}
            <div className="flex items-center gap-2">
              <button 
                onClick={handleFilterClick}
                data-filter-trigger="true"
                className="flex items-center gap-2 text-sm text-foreground-secondary hover:text-foreground transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                Filters
              </button>

              {/* Active filters */}
              <div className="flex items-center gap-1">
                <div className="flex items-center gap-1 overflow-x-auto 
                  [&::-webkit-scrollbar]:h-0.5
                  [&::-webkit-scrollbar-track]:bg-transparent
                  [&::-webkit-scrollbar-thumb]:bg-foreground/5
                  [&::-webkit-scrollbar-thumb]:hover:bg-foreground/10
                  [&::-webkit-scrollbar-thumb]:rounded-full
                  [&::-webkit-scrollbar-track]:rounded-full
                  dark:[&::-webkit-scrollbar-thumb]:bg-white/5
                  dark:[&::-webkit-scrollbar-thumb]:hover:bg-white/10
                  scrollbar-thin
                  scrollbar-track-transparent
                  scrollbar-thumb-foreground/5
                  hover:scrollbar-thumb-foreground/10"
                >
                  {activeFilters.slice(0, visibleFilters).map(filter => (
                    <Badge 
                      key={filter.id} 
                      variant="secondary" 
                      className="flex-shrink-0 flex items-center gap-1 whitespace-nowrap py-0.5 text-xs bg-muted/10"
                    >
                      {filter.icon && <filter.icon className="h-3 w-3" />}
                      {filter.label}
                      <button
                        onClick={() => removeFilter(filter.id)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                  {activeFilters.length > visibleFilters && (
                    <Badge 
                      variant="secondary"
                      className="flex-shrink-0 whitespace-nowrap py-0.5 text-xs bg-muted/10 cursor-pointer"
                      onClick={handleFilterClick}
                    >
                      +{activeFilters.length - visibleFilters} more
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Right side - Character counter */}
            <div className="text-sm text-foreground-secondary">
              {message.length}/{MAX_CHARS}
            </div>
          </div>
        </div>
      </form>

      <FilterCommand 
        projectId={selectedProjectId}
        open={isFilterOpen}
        onOpenChange={setIsFilterOpen}
        activeFilters={activeFilters}
        onActiveFiltersChange={setActiveFilters}
      />
    </div>
  );
};

export default ChatInput;
