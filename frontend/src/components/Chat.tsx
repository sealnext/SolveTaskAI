import React, { useRef, useEffect, useState } from 'react';
import DOMPurify from 'dompurify';
import { MdSupportAgent } from "react-icons/md";

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
}

interface ChatProps {
  messages: Message[];
}

const Chat: React.FC<ChatProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [typingMessage, setTypingMessage] = useState<Message | null>(null);
  const [lastMessageId, setLastMessageId] = useState<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      setLastMessageId(lastMessage.id);
      if (lastMessage.sender === 'ai') {
        setTypingMessage(lastMessage);
      }
    }
  }, [messages]);

  const formatJiraTickets = (text: string) => {
    return text.replace(/JIRA-\d+/g, (match) => 
      `<span class="text-blue-500 cursor-pointer">${match}</span>`
    );
  };

  const TypewriterEffect: React.FC<{ message: Message }> = ({ message }) => {
    const [displayText, setDisplayText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
      if (currentIndex < message.text.length) {
        const timer = setTimeout(() => {
          setDisplayText(prev => formatJiraTickets(prev + message.text[currentIndex]));
          setCurrentIndex(prevIndex => prevIndex + 1);
        }, 20);

        return () => clearTimeout(timer);
      } else {
        setTypingMessage(null);
      }
    }, [currentIndex, message.text]);

    return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(displayText) }} />;
  };

  return (
    <div className="bg-background fixed inset-0 flex items-center justify-center px-4 pt-6 pb-28">
      <div className="w-3/4 max-w-4xl h-full flex flex-col">
        <div className="flex-grow border-gray-200 dark:border-gray-700 border-2 overflow-hidden bg-white dark:bg-backgroundSecondary rounded-xl shadow-md">
          <div className="h-full overflow-y-auto custom-scrollbar">
            <div className="space-y-2 px-12 py-8">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start items-start'} px-8 ${
                    message.id === lastMessageId ? 'animate-fade-in' : ''
                  }`}
                >
                  {message.sender === 'ai' && (
                    <div className="mr-2 mt-1">
                      <div className="w-7 h-7 rounded-full border-2 border-gray-700 dark:border-gray-300 flex items-center justify-center">
                        <MdSupportAgent className="text-gray-700 dark:text-gray-300 text-lg" />
                      </div>
                    </div>
                  )}
                  <div
                    className={`rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-gray-800 dark:bg-gray-700 rounded-xl text-white border border-gray-600 dark:border-gray-500'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                    } max-w-[70%]`}
                  >
                    {message.sender === 'ai' && typingMessage?.id === message.id ? (
                      <TypewriterEffect message={message} />
                    ) : (
                      <div dangerouslySetInnerHTML={{ 
                        __html: DOMPurify.sanitize(formatJiraTickets(message.text)) 
                      }} />
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;