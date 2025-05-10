import React from 'react';
import { Share } from 'lucide-react';

const ChatHeader: React.FC = () => {
  return (
    <div className="flex justify-between items-center px-4 py-2 border-b border-gray-200">
      <div className="flex items-center space-x-2">
        <button className="text-gray-500 p-1 rounded hover:bg-gray-100">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
          </svg>
        </button>
      </div>
      <button className="flex items-center space-x-1 px-3 py-1.5 rounded-md hover:bg-gray-100 transition-colors">
        <Share className="h-5 w-5 text-gray-600" />
        <span className="text-sm font-medium">Share</span>
      </button>
    </div>
  );
};

export default ChatHeader;