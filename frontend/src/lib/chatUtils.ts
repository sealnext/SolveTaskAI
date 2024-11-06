import { isToday, isYesterday } from "date-fns"

export interface ChatSession {
  id: string
  project_id?: number
  created_at: string
  preview: string
  message_count: number
}

export function groupChatsByDate(chats: ChatSession[]) {
  if (!chats || !Array.isArray(chats)) {
    return {} as Record<string, ChatSession[]>
  }

  const grouped = chats.reduce((acc, chat) => {
    const date = new Date(chat.created_at)
    let key = 'Older'
    
    if (isToday(date)) key = 'Today'
    else if (isYesterday(date)) key = 'Yesterday'
    
    if (!acc[key]) acc[key] = []
    acc[key].push(chat)
    return acc
  }, {} as Record<string, ChatSession[]>)

  return grouped
}

export function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
} 