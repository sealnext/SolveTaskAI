import React, { useState } from 'react';
import ChatMessage from './chat-message';
import ChatInput from './chat-input';

interface Message {
  id: number;
  isBot: boolean;
  content: string;
  status?: 'sending' | 'sent' | 'error';
  timestamp?: Date;
}

const initialMessages: Message[] = [
  {
    id: 1,
    isBot: true,
    content: "Hello! How can I help you today?",
    status: 'sent',
    timestamp: new Date(Date.now() - 60000)
  }
];

const ChatContent: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);

  const handleSendMessage = (message: string) => {
    const newMessage: Message = {
      id: messages.length + 1,
      isBot: false,
      content: message,
      status: 'sending',
      timestamp: new Date()
    };

    setMessages([...messages, newMessage]);
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        <div className="max-w-2xl mx-auto w-full space-y-6">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
            />
          ))}
        </div>
      </div>
      
      {/* Input */}
      <div className="p-4 sticky bottom-0 z-10">
        <div className="max-w-2xl mx-auto">
          <ChatInput onSendMessage={handleSendMessage} />
        </div>
      </div>
    </div>
  );
};

export default ChatContent;
