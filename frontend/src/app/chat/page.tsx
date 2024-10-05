'use client'

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from 'react'
import { LoadingSpinner } from "@/components/LoadingSpinner"
import SpatialTooltip from "@/components/SpatialTooltip"
import ChatInput from "@/components/ChatInput"
import Chat from "@/components/Chat"
import { v4 as uuidv4 } from 'uuid'; // Asigurați-vă că aveți instalat pachetul uuid

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
}

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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

      // Simulăm un răspuns de la AI pentru demonstrație
      await new Promise(resolve => setTimeout(resolve, 2500));
      const aiResponse: Message = {
        id: uuidv4(),
        text: `AI response to: "${message}"`,
        sender: 'ai'
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
      <SpatialTooltip />
      
      <div className="flex-grow overflow-hidden">
        <Chat messages={messages} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}