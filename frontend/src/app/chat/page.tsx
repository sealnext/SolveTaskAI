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

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  isHtml?: boolean;
}

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const apiclient = ApiClient();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push('/login');
    }
  }, [status, router]);

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
     
      const response = await apiclient.get('/projects/all');
      console.log(response);
      
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

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}