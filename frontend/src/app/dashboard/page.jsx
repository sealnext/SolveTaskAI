'use client'

import { useSession } from "next-auth/react";
import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { ChevronLeft, ChevronRight, MessageSquarePlus, History, FolderOpen, MessageCircle, ThumbsUp, Send } from 'lucide-react'
import { ProfileMenuComponent } from "@/components/profile-menu"

export default function Component() {
  const { data: session } = useSession();
  const [sidebarState, setSidebarState] = useState('open')
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! How can I help you today?", sender: "bot" },
    { id: 2, text: "I have a question about SEALNEXT.", sender: "user" },
    { id: 3, text: "Sure, I'd be happy to help. What would you like to know about SEALNEXT?", sender: "bot" },
  ])
  const [inputMessage, setInputMessage] = useState("")

  const toggleSidebar = () => {
    setSidebarState(sidebarState === 'open' ? 'closed' : 'open')
  }

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      setMessages([...messages, { id: messages.length + 1, text: inputMessage, sender: "user" }])
      setInputMessage("")
    }
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <div 
        className={`relative transition-all duration-300 ease-in-out ${
          sidebarState === 'open' ? 'w-64' : 'w-16'
        }`}
        onMouseEnter={() => sidebarState === 'closed' && setSidebarState('mini')}
        onMouseLeave={() => sidebarState === 'mini' && setSidebarState('closed')}
      >
        <div className={`absolute top-0 left-0 h-full overflow-hidden transition-all duration-300 ease-in-out ${
          sidebarState === 'open' ? 'w-64' : 'w-16'
        } bg-secondary`}>
          <div className="flex flex-col h-full">
            {/* Logo and Toggle Button */}
            <div className="p-4 flex items-center justify-between">
              {sidebarState === 'open' && <div className="font-bold text-xl">SEALNEXT</div>}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleSidebar}
              >
                {sidebarState === 'open' ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </div>

            {/* New Chat Button */}
            <Button 
              className={`m-2 flex items-center justify-${sidebarState === 'open' ? 'start' : 'center'}`} 
              variant="outline"
            >
              <MessageSquarePlus className="h-4 w-4" />
              {sidebarState === 'open' && <span className="ml-2">New Chat</span>}
            </Button>

            {/* Navigation Items */}
            <ScrollArea className="flex-grow px-2">
              <div className="space-y-2">
                <Button variant="ghost" className={`w-full justify-${sidebarState === 'open' ? 'start' : 'center'}`}>
                  <History className="h-4 w-4" />
                  {sidebarState === 'open' && <span className="ml-2">Chat History</span>}
                </Button>
                <Button variant="ghost" className={`w-full justify-${sidebarState === 'open' ? 'start' : 'center'}`}>
                  <FolderOpen className="h-4 w-4" />
                  {sidebarState === 'open' && <span className="ml-2">Projects</span>}
                </Button>
                <Button variant="ghost" className={`w-full justify-${sidebarState === 'open' ? 'start' : 'center'}`}>
                  <ThumbsUp className="h-4 w-4" />
                  {sidebarState === 'open' && <span className="ml-2">Feedback</span>}
                </Button>
              </div>

              {sidebarState === 'open' && (
                <>
                  <Separator className="my-4" />

                  {/* Recent Chats */}
                  <div>
                    <h3 className="mb-2 px-2 text-sm font-semibold">Recent Chats</h3>
                    <div className="space-y-2">
                      {['Chat 1', 'Chat 2', 'Chat 3'].map((chat, index) => (
                        <Button key={index} variant="ghost" className="w-full justify-start">
                          <MessageCircle className="mr-2 h-4 w-4" />
                          {chat}
                        </Button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </ScrollArea>

            {/* User Account - Replace with ProfileMenuComponent */}
            {sidebarState === 'open' && (
              <div className="p-4 border-t">
                <ProfileMenuComponent />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area (Chat) */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages */}
        <ScrollArea className="flex-1 p-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 ${
                message.sender === 'user' ? 'text-right' : 'text-left'
              }`}
            >
              <div
                className={`inline-block p-2 rounded-lg ${
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary'
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
        </ScrollArea>

        {/* Message Input */}
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <Input
              type="text"
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <Button onClick={handleSendMessage}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}