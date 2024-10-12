'use client'

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from 'react'
import { LoadingSpinner } from "@/components/LoadingSpinner"
import SpatialTooltip from "@/components/SpatialTooltip"
import ChatInput from "@/components/ChatInput"
import Chat from "@/components/Chat"
import { v4 as uuidv4 } from 'uuid';
import { ProfileMenuComponent } from "@/components/profile-menu";
import ApiClient from "@/lib/apiClient";
import ProjectSelector from "@/components/ProjectSelector";

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  isHtml?: boolean;
}

interface Project {
  id: number;
  name: string;
  service_type: string;
  company_id: number;
  domain: string;
}

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const apiclient = ApiClient();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await apiclient.get('/projects/internal');
        setProjects(response);
        if (response.length === 1) {
          setSelectedProjectId(response[0].id);
        }
      } catch (error) {
        console.error('Error fetching projects:', error);
      }
    };

    fetchProjects();
  }, []);

  const handleProjectSelect = (projectId: number) => {
    setSelectedProjectId(projectId);
  };

  const handleSendMessage = useCallback(async (message: string) => {
    const newUserMessage: Message = {
      id: uuidv4(),
      text: message,
      sender: 'user'
    };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setIsLoading(true);

    try {
      // Aici ar trebui să fie apelul real către API
      // const data = await response.json();
     
      const response = await apiclient.post('/projects/external', {
        service_type: "jira",
        api_key: "YOUR_ATLASSIAN_TOKEN_HERE",
        domain: "https://sealnext.atlassian.net/",
        domain_email: "ovidiu@sealnext.com"
      });
      // [
      //     {
      //       "name": "project zugravii",
      //       "key": "PZ",
      //       "id": "10001",
      //       "avatarUrl": "https://sealnext.atlassian.net/rest/api/2/universal_avatar/view/type/project/avatar/10418",
      //       "projectTypeKey": "software",
      //       "style": "next-gen"
      //   },
      //   {
      //       "name": "ScrumProjectNr1",
      //       "key": "SCRUM",
      //       "id": "10000",
      //       "avatarUrl": "https://sealnext.atlassian.net/rest/api/2/universal_avatar/view/type/project/avatar/10402",
      //       "projectTypeKey": "software",
      //       "style": "next-gen"
      //   }
      // ]
      
      const local_projects = await apiclient.get('/projects/internal');
      //   [
      //     {
      //         "id": 1,
      //         "name": "test",
      //         "domain": "https://sealnext.atlassian.net/",
      //         "company_id": 1
      //     }
      //  ]

      // Simulăm un răspuns de la AI pentru demonstrație
      await new Promise(resolve => setTimeout(resolve, 2500));
      const aiResponse: Message = {
        id: uuidv4(),
        text: `The User Registration Bug (JIRA-3005) is being fixed, expected by October 10, 2024. The Payment Gateway Integration (JIRA-3010) is complete as of October 3, 2024.`,
        sender: 'ai',
        isHtml: true
      };

      setMessages(prevMessages => [...prevMessages, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Aici puteți adăuga o notificare de eroare pentru utilizator
    } finally {
      setIsLoading(false);
    }
  }, []);

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
        <Chat messages={messages} />
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
        />
      </div>
    </div>
  )
}
