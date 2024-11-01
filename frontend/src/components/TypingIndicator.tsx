'use client'

export default function TypingIndicator() {
  return (
    <div className="flex items-center space-x-2 p-4">
      <div className="flex space-x-2">
        <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce" 
             style={{ animationDelay: '0ms' }}></div>
        <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce" 
             style={{ animationDelay: '150ms' }}></div>
        <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce" 
             style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
} 