'use client'

import { useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, useMemo } from 'react'
import { LoadingSpinner } from "@/components/LoadingSpinner"
import SpatialTooltip from "@/components/SpatialTooltip"
import ChatInput from "@/components/ChatInput"
import Chat from "@/components/Chat"
import { v4 as uuidv4 } from 'uuid';
import { ProfileMenuComponent } from "@/components/menu/ProfileMenu";
import ApiClient from "@/lib/apiClient";
import ProjectSelector from "@/components/ProjectSelector";
import ProjectManager from "@/components/ProjectManagerPopup/ProjectManager";
import { MobileSidebar } from "@/components/MobileSidebar"

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
  }, []);

  useEffect(() => {
    fetchInternalProjects();
  }, [fetchInternalProjects]);

  const handleProjectSelect = (projectId: number) => {
    setSelectedProjectId(projectId);
  };

  const handleSendMessage = useCallback(async (message: string) => {
    if (!selectedProjectId) {
      throw new Error("Please select a project before sending a message");
      // TODO: IMPLEMENT A POPUP TO SELECT A PROJECT
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

  useEffect(() => {
    const loadExistingChat = async () => {
      if (chatId) {
        try {
          const response = await apiclient.get(`/chat/${chatId}`);
          const chatHistory = response.data.messages.map((msg: any) => ({
            id: uuidv4(),
            text: msg.content,
            sender: msg.role === 'human' ? 'user' : 'ai',
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

  const handleNewChat = useCallback(() => {
    router.push('/chat');
  }, [router]);

  if (status === "loading") {
    return <LoadingSpinner />;
  }

  if (!session) {
    return null;
  }

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      {/* Sidebar overlay */}
      <div className="absolute top-0 left-0 z-50">
        <MobileSidebar 
          selectedChatId={chatId || null}
          onSelectChat={(chatId: string) => router.push(`/chat?chat_id=${chatId}`)}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main content */}
      <main className="min-h-screen flex flex-col">
        <div className="absolute top-4 right-4 z-50">
          <ProfileMenuComponent />
        </div>

        <SpatialTooltip />
        
        {/* Chat container - using absolute positioning to maximize height */}
        <div className="absolute inset-0 pt-16 pb-32">
          <div className="h-full w-[95%] md:w-3/4 max-w-4xl mx-auto">
            <Chat messages={messages} loadingMessage={loadingMessage} />
          </div>
        </div>

        {/* Chat input */}
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 w-[95%] md:w-3/4 max-w-4xl z-10">
          <ChatInput 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading}
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
      </main>
    </div>
  )
}
