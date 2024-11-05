import React, { useState, useRef, KeyboardEvent } from 'react';
import ProjectSelector from './ProjectSelector';
import { Project } from '@/types/project';
import { useSearchParams } from 'next/navigation';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onAddNewProject: () => void;
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

  return (
    <form onSubmit={handleSubmit} className="relative h-14">
      <div className="h-full bg-backgroundSecondary bg-opacity-80 backdrop-filter backdrop-blur-md text-foreground rounded-2xl px-4 flex items-center justify-between shadow-lg border-muted border-2 transition-all duration-300">
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
            />
          </div>
        </div>

        {/* Project Selector and Send button container */}
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

          {/* Project Selector - afișăm doar dacă nu există chat_id */}
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
    </form>
  );
};

export default ChatInput;
