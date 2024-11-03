import React, { useRef, useEffect, useState } from 'react';
import DOMPurify from 'dompurify';
import { MdSupportAgent } from "react-icons/md";

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  isHtml?: boolean;
  animate?: boolean;
}

interface ChatProps {
  messages: Message[];
  loadingMessage?: Message;
}

const Chat: React.FC<ChatProps> = ({ messages, loadingMessage }) => {
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
      if (lastMessage.sender === 'ai' && lastMessage.animate) {
        setTypingMessage(lastMessage);
      }
    }
  }, [messages]);

  const formatJiraTickets = (text: string) => {
    const jiraPattern = /\[(.*?)]\((https?:\/\/[^\s)]+)\)/g;
    return text.replace(jiraPattern, (match, linkText, url) => 
      `<a href="${url}" target="_blank" class="text-blue-500 hover:underline">${linkText}</a>`
    );
  };

  const formatText = (text: string) => {
    let processedText = text
      .replace(/\\n\\n/g, '\n\n')
      .replace(/\\n/g, '\n');
    
    processedText = processedText
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    
    processedText = formatJiraTickets(processedText);

    processedText = processedText
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">$1</code>')
      .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto"><code>$1</code></pre>');

    return processedText;
  };

  const formatMessage = (message: Message) => {
    const formattedText = formatText(message.text);
    
    return (
      <div 
        className="markdown-content"
        dangerouslySetInnerHTML={{ 
          __html: DOMPurify.sanitize(formattedText, {
            ALLOWED_TAGS: ['strong', 'em', 'code', 'pre', 'a', 'br'],
            ALLOWED_ATTR: ['href', 'target', 'class']
          }) 
        }} 
      />
    );
  };

  const TypewriterEffect: React.FC<{ message: Message }> = ({ message }) => {
    const [displayText, setDisplayText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
      if (currentIndex < message.text.length) {
        const timer = setTimeout(() => {
          setDisplayText(prev => prev + message.text[currentIndex]);
          setCurrentIndex(prevIndex => prevIndex + 1);
        }, 20);

        return () => clearTimeout(timer);
      } else {
        setTypingMessage(null);
      }
    }, [currentIndex, message.text]);

    return formatMessage({ ...message, text: displayText });
  };

  return (
    <div className="bg-background fixed inset-0 flex items-center justify-center px-4 pt-6 pb-28">
      <div className="w-3/4 max-w-4xl h-full flex flex-col">
        <div className="flex-grow border-muted border-2 overflow-hidden bg-backgroundSecondary rounded-xl shadow-md">
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
                      <div className="w-7 h-7 rounded-full border-2 border-muted flex items-center justify-center">
                        <MdSupportAgent className="text-foreground-secondary text-lg" />
                      </div>
                    </div>
                  )}
                  <div
                    className={`rounded-xl p-3 ${
                      message.sender === 'user'
                        ? 'bg-accent text-foreground'
                        : 'bg-backgroundSecondary text-foreground'
                    } max-w-[70%]`}
                  >
                    {message.sender === 'ai' && message.animate && typingMessage?.id === message.id ? (
                      <TypewriterEffect message={message} />
                    ) : (
                      formatMessage(message)
                    )}
                  </div>
                </div>
              ))}
              
              {loadingMessage && (
                <div className="flex justify-start items-start px-8 animate-fade-in">
                  <div className="mr-2 mt-1">
                    <div className="w-7 h-7 rounded-full border-2 border-muted flex items-center justify-center">
                      <MdSupportAgent className="text-foreground-secondary text-lg" />
                    </div>
                  </div>
                  <div className="rounded-xl p-3 bg-backgroundSecondary text-foreground max-w-[70%]">
                    <div className="flex items-center space-x-1">
                      <span className="animate-bounce">.</span>
                      <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
                      <span className="animate-bounce" style={{ animationDelay: "0.4s" }}>.</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;