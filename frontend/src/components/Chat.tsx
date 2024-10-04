import React, { useRef, useEffect, useState } from 'react';

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
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [typingMessage, setTypingMessage] = useState<Message | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].sender === 'ai') {
      setTypingMessage(messages[messages.length - 1]);
    }
  }, [messages]);

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

    return <p className="text-sm">{displayText}</p>;
  };

  return (
    <div className="bg-[#f4f4f4] fixed inset-0 flex items-center justify-center px-4 pt-6 pb-28">
      <div className="w-3/4 max-w-4xl h-full flex flex-col">
        <div className="flex-grow border-gray-200 border-2 overflow-hidden bg-white rounded-xl shadow-md">
          <div 
            ref={chatContainerRef}
            className="h-full overflow-y-auto custom-scrollbar"
          >
            <div className="space-y-2 px-12 py-8">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} message-appear px-8`}
                >
                  <div
                    className={`p-2 rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-gray-800 rounded-xl text-white border border-gray-600'
                        : 'text-gray-800'
                    } max-w-[70%]`}
                  >
                    {message.sender === 'ai' && typingMessage?.id === message.id ? (
                      <TypewriterEffect message={message} />
                    ) : (
                      <p className="text-sm">{message.text}</p>
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