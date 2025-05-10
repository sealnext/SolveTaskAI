
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Smile } from 'lucide-react';
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import { Card } from "~/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <TooltipProvider>
      <Card className="p-2 border shadow-md bg-sidebar">
        <div className="flex items-end space-x-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground">
                <Paperclip className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Attach file</TooltipContent>
          </Tooltip>
          
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 resize-none border-0 min-h-9 py-1 focus-visible:ring-0 shadow-none flex items-center justify-center"
            placeholder="Type a message..."
            rows={1}
          />
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground">
                <Smile className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Emoji</TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground">
                <Mic className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Voice</TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={handleSendMessage}
                disabled={!message.trim()}
                variant={message.trim() ? "default" : "secondary"}
                size="icon"
                className="rounded-full"
              >
                <Send className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Send</TooltipContent>
          </Tooltip>
          
        </div>
      </Card>
    </TooltipProvider>
  );
};

export default ChatInput;
