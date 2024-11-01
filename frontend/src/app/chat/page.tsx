'use client'

import { useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, useMemo } from 'react'
import { LoadingSpinner } from "@/components/LoadingSpinner"
import SpatialTooltip from "@/components/SpatialTooltip"
import ChatInput from "@/components/ChatInput"
import Chat from "@/components/Chat"
import { v4 as uuidv4 } from 'uuid';
import { ProfileMenuComponent } from "@/components/ProfileMenu";
import ApiClient from "@/lib/apiClient";
import ProjectSelector from "@/components/ProjectSelector";
import ProjectManager from "@/components/ProjectManagerPopup/ProjectManager";

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  isHtml?: boolean;
  animate?: boolean;
}

interface Project {
  id: number;
  name: string;
  service_type: string;
  domain: string;
}

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const chatId = searchParams.get('chat_id');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [showProjectManager, setShowProjectManager] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<Message | null>(null);

  // Memoize the API client to prevent it from being recreated on each render
  const apiclient = useMemo(() => ApiClient(), []);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push('/login');
    }
  }, [status, router]);

  const fetchInternalProjects = useCallback(async () => {
    try {
      const response = await apiclient.get('/projects/internal');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching internal projects:', error);
    }
  }, []); // Remove apiclient from the dependency array

  useEffect(() => {
    fetchInternalProjects();
  }, [fetchInternalProjects]);

  const handleProjectSelect = (projectId: number) => {
    setSelectedProjectId(projectId);
  };

  const handleSendMessage = useCallback(async (message: string) => {
    if (!selectedProjectId) {
      return;
    }

    const newUserMessage: Message = {
      id: uuidv4(),
      text: message,
      sender: 'user'
    };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    
    setLoadingMessage({
      id: 'loading',
      text: '',
      sender: 'ai'
    });
    setIsLoading(true);

    try {
      const requestBody = {
        question: message,
        project_id: selectedProjectId,
        user_id: session?.user?.id,
        ...(chatId && { chat_id: chatId })
      };

      const response = await apiclient.post('/chat', requestBody);
      const { answer, chat_id } = response.data;

      if (!chatId) {
        router.push(`/chat?chat_id=${chat_id}`);
      }

      const aiResponse: Message = {
        id: uuidv4(),
        text: answer,
        sender: 'ai',
        isHtml: true,
        animate: true
      };

      setMessages(prevMessages => [...prevMessages, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoadingMessage(null);
      setIsLoading(false);
    }
  }, [selectedProjectId, chatId, session?.user?.id, router, apiclient]);

  // Add a useEffect to load existing chat messages if chat_id exists
  useEffect(() => {
    const loadExistingChat = async () => {
      if (chatId) {
        try {
          const response = await apiclient.get(`/chat/${chatId}`);
          const chatHistory = response.data.messages.map((msg: any) => ({
            id: uuidv4(),
            text: msg.content,
            sender: msg.role === 'user' ? 'user' : 'ai',
            isHtml: msg.role === 'ai',
            animate: false
          }));
          setMessages(chatHistory);
          
          if (response.data.project_id) {
            setSelectedProjectId(response.data.project_id);
          }
          
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      } else {
        // Clear messages for new chat
        setMessages([]);
      }
    };

    loadExistingChat();
  }, [chatId, apiclient]);

  const handleCloseApiKeyManager = () => {
    setShowProjectManager(false);
  };

  const handleProjectsUpdate = useCallback((newProjects: Project[]) => {
    setProjects(newProjects);
  }, []);

  const refreshInternalProjects = useCallback(async () => {
    try {
      const response = await apiclient.get('/projects/internal');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching internal projects:', error);
    }
  }, [apiclient]);

  if (status === "loading") {
    return <LoadingSpinner />;
  }

  if (!session) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen bg-background text-foreground relative">
      <div className="absolute top-4 right-4 z-50">
        <ProfileMenuComponent />
      </div>
      <SpatialTooltip />
      
      <div className="flex-grow overflow-hidden">
        <Chat messages={messages} loadingMessage={loadingMessage} />
      </div>

      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-3/4 max-w-4xl flex items-center space-x-4">
        <div className="flex-grow h-14">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>

      <div className="fixed bottom-8 right-4 w-1/8 h-14">
        <ProjectSelector 
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelectProject={handleProjectSelect}
          onAddNewProject={() => setShowProjectManager(true)}
        />
      </div>

      {showProjectManager && (
        <ProjectManager 
          projects={projects} 
          onProjectsUpdate={handleProjectsUpdate}
          onClose={handleCloseApiKeyManager}
          refreshInternalProjects={refreshInternalProjects}
        />
      )}
    </div>
  )
}
