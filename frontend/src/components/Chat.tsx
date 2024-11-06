import React, { useRef, useEffect, useState } from 'react';
import DOMPurify from 'dompurify';
import { MdSupportAgent } from "react-icons/md";
import { GridIcon } from '@/components/WaitingMessage';

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

  const EmptyStateMessage = () => (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
      <div className="relative mb-2">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-primary/40 rounded-full blur-2xl" />
        <div className="relative bg-background/95 backdrop-blur-sm rounded-full p-3">
          <MdSupportAgent className="text-4xl md:text-5xl text-primary" />
        </div>
      </div>
      
      <div className="space-y pb-2 max-w-xl px-2">
        <h3 className="text-lg md:text-xl font-bold text-foreground">
          Hello! I'm your AI Development Assistant
        </h3>
        <p className="text-sm md:text-base text-muted-foreground">
          I can help you with code analysis, task management, and development best practices
        </p>
      </div>

      <div className="grid grid-cols-2 gap-x-2 gap-y-8 md:gap-4 w-full md:px-4 max-w-2xl">
        <ExampleCard
          title="Code Analysis"
          description="Get code insights"
          example="Review the PR code from this task for potential security vulnerabilities and suggest optimizations"
        />
        <ExampleCard
          title="Task Management"
          description="Break down work"
          example="Break down this epic into smaller, estimated tasks with acceptance criteria"
        />
        <ExampleCard
          title="Implementation Guide"
          description="Task & documentation help"
          example="Help me understand the high-level implementation flow across these related tasks"
        />
        <ExampleCard
          title="Documentation Search"
          description="Find project info"
          example="Can you search through our project docs and explain how we handle user roles and permissions?"
        />
      </div>
    </div>
  );

  interface ExampleCardProps {
    title: string;
    description: string;
    example: string;
  }

  const ExampleCard = ({ title, description, example }: ExampleCardProps) => (
    <div className="group relative h-auto min-h-[130px] md:h-[160px]">
      <div className="absolute hidden md:block -inset-0.5 bg-gradient-to-r from-primary/30 to-primary/20 rounded-lg md:rounded-xl blur opacity-75 group-hover:opacity-100 transition duration-500" />
      <div className="relative h-full md:bg-gray-50 dark:md:bg-muted/50 md:hover:bg-gray-100 dark:md:hover:bg-muted/70 p-3 md:p-4 md:rounded-lg transition duration-200 md:border md:border-primary/10 md:hover:border-primary/20 flex flex-col">
        <div>
          <h4 className="text-base md:text-base font-semibold text-foreground border-b border-primary/10 pb-1 mb-1 md:border-none md:pb-0 md:mb-0">
            {title}
          </h4>
          <p className="text-sm hidden md:block md:text-xs text-muted-foreground/80 mt-1 md:mt-0.5">
            {description}
          </p>
        </div>
        <div className="mb-auto pt-2">
          <div 
            className="group/item flex items-start space-x-2 md:space-x-2 text-sm md:text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <span className="md:text-sm text-xs">{example}</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-background fixed inset-0 flex items-center justify-center px-4 pt-6 pb-28">
      <div className="w-3/4 max-w-4xl h-full flex flex-col md:w-3/4 w-full">
        <div className="flex-grow border-muted md:border-2 overflow-hidden bg-backgroundSecondary rounded-xl md:border-2 md:bg-backgroundSecondary md:rounded-xl md:shadow-md border-0 bg-transparent">
          <div className="h-full overflow-y-auto custom-scrollbar">
            {messages.length === 0 ? (
              <EmptyStateMessage />
            ) : (
              <div className="space-y-2 md:px-8 py-8">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start items-start'} md:px-8 ${
                      message.id === lastMessageId ? 'animate-fade-in' : ''
                    }`}
                  >
                    {message.sender === 'ai' && (
                      <div className="mt-2">
                        <div className="w-7 h-7 rounded-full border-2 border-muted flex items-center justify-center">
                          <MdSupportAgent className="text-foreground-secondary text-lg" />
                        </div>
                      </div>
                    )}
                    <div
                      className={`rounded-xl p-3 ${
                        message.sender === 'ai' 
                          ? 'md:bg-backgroundSecondary bg-transparent md:max-w-[90%] max-w-[90%]' 
                          : 'bg-accent md:max-w-[70%] max-w-[70%]'
                      } text-foreground`}
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
                  <div className="flex justify-start items-start md:px-8 animate-fade-in">
                    <div className="mt-2">
                      <div className="w-7 h-7 rounded-full border-2 border-muted flex items-center justify-center">
                        <MdSupportAgent className="text-foreground-secondary text-lg" />
                      </div>
                    </div>
                    <div className="rounded-xl p-3 text-foreground max-w-[70%]">
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
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;