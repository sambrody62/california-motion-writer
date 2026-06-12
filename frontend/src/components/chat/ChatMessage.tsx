import React from 'react';
import { User, Bot, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

interface MessageProps {
  message: {
    id: string;
    content: string;
    sender: 'user' | 'assistant' | 'system';
    timestamp: string;
    attachments?: any[];
  };
}

const ChatMessage: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const isSystem = message.sender === 'system';

  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'h:mm a');
    } catch {
      return '';
    }
  };

  if (isSystem) {
    return (
      <div className="flex items-center justify-center space-x-2 text-sm text-yellow-600 bg-yellow-50 px-3 py-2 rounded-lg">
        <AlertCircle size={16} />
        <span>{message.content}</span>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
        }`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}>
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </div>
          <span className="text-xs text-gray-400 mt-1">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;