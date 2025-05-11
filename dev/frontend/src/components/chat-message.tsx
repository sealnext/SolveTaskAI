import React from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageSquare, User } from 'lucide-react';
import { Avatar, AvatarFallback } from 'src/components/ui/avatar';
import { cn } from 'src/lib/utils';

interface Message {
	id: number;
	isBot: boolean;
	content: string;
	status?: 'sending' | 'sent' | 'error';
}

interface MessageProps {
	message: Message;
}

export function ChatMessage({ message }: MessageProps) {
	return (
		<div className={cn('flex gap-3 mb-4', message.isBot ? '' : 'flex-row-reverse')}>
			<Avatar className="h-8 w-8 shrink-0">
				<AvatarFallback>
					{message.isBot ? (
						<MessageSquare className="h-4 w-4 text-primary" />
					) : (
						<User className="h-4 w-4 text-primary" />
					)}
				</AvatarFallback>
			</Avatar>

			<div
				className={cn(
					'flex flex-col max-w-[80%] md:max-w-[70%]',
					message.isBot ? 'items-start' : 'items-end',
				)}
			>
				<div className="rounded-lg p-3 shadow-sm bg-muted">
					<ReactMarkdown>{message.content}</ReactMarkdown>
				</div>

				{message.status === 'sending' && (
					<span className="text-xs text-muted-foreground mt-1">Sending...</span>
				)}
			</div>
		</div>
	);
}
