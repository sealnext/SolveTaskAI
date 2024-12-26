'use client'

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useMemo } from 'react'
import { LoadingSpinner } from "@/components/LoadingSpinner"
import { ProfileMenuComponent } from "@/components/menu/ProfileMenu";
import SpatialTooltip from "@/components/SpatialTooltip"
import ApiClient from "@/lib/apiClient";
import { MdSupportAgent, MdAccessTime, MdMessage } from "react-icons/md";
import { ChatSession, groupChatsByDate, formatTime } from "@/lib/chatUtils"

export default function HistoryPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const apiclient = useMemo(() => ApiClient(), []);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await apiclient.post('/chat/history', {});
        setChatSessions(response.data.chat_sessions);
      } catch (error) {
        console.error('Error fetching chat history:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (session) {
      fetchChatHistory();
    }
  }, [session, apiclient]);

  const groupedChats = groupChatsByDate(chatSessions);

  const handleChatSelect = (chatId: string) => {
    router.push(`/chat?chat_id=${chatId}`);
  };

  if (status === "loading" || isLoading) {
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

      <div className="flex-grow overflow-auto p-6 sm:p-6 p-3">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-bold">Chat History</h1>
          </div>

          <div className="space-y-8">
            {Object.entries(groupedChats).map(([dateGroup, chats]) => (
              <div key={dateGroup}>
                <h3 className="text-sm font-medium text-muted-foreground mb-4">
                  {dateGroup}
                </h3>
                <div className="space-y-4">
                  {chats.map((chat) => (
                    <div
                      key={chat.id}
                      onClick={() => handleChatSelect(chat.id)}
                      className="bg-backgroundSecondary rounded-xl p-4 shadow-md hover:shadow-lg transition-all hover:scale-[1.01] cursor-pointer border border-muted"
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full border-2 border-muted flex items-center justify-center flex-shrink-0 bg-background">
                          <MdSupportAgent className="text-foreground-secondary text-xl sm:text-2xl" />
                        </div>

                        <div className="flex-grow min-w-0">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2">
                            <div className="font-medium truncate flex-grow max-w-full sm:max-w-[70%]">
                              {chat.preview}
                            </div>
                            <div className="text-xs sm:text-sm text-foreground-secondary flex items-center sm:ml-4 mt-1 sm:mt-0">
                              <MdAccessTime className="mr-1" />
                              {formatTime(chat.created_at)}
                            </div>
                          </div>

                          <div className="flex items-center text-xs sm:text-sm text-foreground-secondary">
                            <MdMessage className="mr-1" />
                            {chat.message_count} messages
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {chatSessions.length === 0 && (
              <div className="text-center text-foreground-secondary py-8">
                No chat history found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
