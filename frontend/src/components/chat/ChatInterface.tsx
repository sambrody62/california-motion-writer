import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, X, Minimize2, Maximize2, MessageCircle } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import ChatMessage from './ChatMessage';
import QuickReplies from './QuickReplies';
import TypingIndicator from './TypingIndicator';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant' | 'system';
  timestamp: string;
  quick_replies?: string[];
  attachments?: any[];
}

interface ChatSession {
  id: string;
  state: string;
  intent?: string;
  confidence?: number;
}

const ChatInterface: React.FC = () => {
  const { user, token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize WebSocket connection
  const initWebSocket = useCallback(() => {
    if (!token || wsConnection?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Send authentication
      ws.send(JSON.stringify({
        type: 'connect',
        data: {
          token,
          session_id: session?.id
        }
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);

      switch (data.type) {
        case 'connected':
          setConnectionStatus('connected');
          break;

        case 'session_created':
          setSession({
            id: data.data.session_id,
            state: data.data.state
          });
          break;

        case 'message':
          setMessages(prev => [...prev, {
            id: data.data.id,
            content: data.data.content,
            sender: 'assistant',
            timestamp: data.data.timestamp,
            quick_replies: data.data.quick_replies
          }]);
          break;

        case 'session_update':
          setSession(prev => ({
            ...prev,
            ...data.data
          }));
          break;

        case 'assistant_typing':
          setIsTyping(data.data.typing);
          break;

        case 'history':
          setMessages(data.data.messages);
          break;

        case 'error':
          console.error('WebSocket error:', data.data.error);
          // Show error message to user
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            content: `Error: ${data.data.error}`,
            sender: 'system',
            timestamp: new Date().toISOString()
          }]);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
      setWsConnection(null);
    };

    setWsConnection(ws);
  }, [token, session?.id]);

  // Open chat and connect
  const openChat = () => {
    setIsOpen(true);
    setIsMinimized(false);
    if (!wsConnection) {
      initWebSocket();
    }
  };

  // Close chat and disconnect
  const closeChat = () => {
    setIsOpen(false);
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
    }
  };

  // Send message
  const sendMessage = () => {
    if (!inputValue.trim() || !wsConnection || connectionStatus !== 'connected') return;

    const message: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    // Add to local messages
    setMessages(prev => [...prev, message]);

    // Send via WebSocket
    wsConnection.send(JSON.stringify({
      type: 'message',
      data: {
        content: inputValue
      }
    }));

    // Clear input
    setInputValue('');
    inputRef.current?.focus();
  };

  // Handle quick reply click
  const handleQuickReply = (reply: string) => {
    setInputValue(reply);
    sendMessage();
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Get latest quick replies
  const latestQuickReplies = messages
    .filter(m => m.quick_replies && m.quick_replies.length > 0)
    .pop()?.quick_replies || [];

  if (!isOpen) {
    return (
      <button
        onClick={openChat}
        className="fixed bottom-4 right-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-200 z-50"
        aria-label="Open chat"
      >
        <MessageCircle size={24} />
      </button>
    );
  }

  return (
    <div className={`fixed bottom-4 right-4 z-50 ${isMinimized ? 'w-64' : 'w-96'}`}>
      <div className="bg-white rounded-lg shadow-2xl flex flex-col" style={{ height: isMinimized ? '60px' : '600px' }}>
        {/* Header */}
        <div className="bg-blue-600 text-white px-4 py-3 rounded-t-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageCircle size={20} />
            <span className="font-semibold">Motion Filing Assistant</span>
            {connectionStatus === 'connecting' && (
              <span className="text-xs bg-yellow-500 px-2 py-1 rounded">Connecting...</span>
            )}
            {connectionStatus === 'disconnected' && (
              <span className="text-xs bg-red-500 px-2 py-1 rounded">Offline</span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="hover:bg-blue-700 p-1 rounded transition-colors"
              aria-label={isMinimized ? 'Maximize' : 'Minimize'}
            >
              {isMinimized ? <Maximize2 size={18} /> : <Minimize2 size={18} />}
            </button>
            <button
              onClick={closeChat}
              className="hover:bg-blue-700 p-1 rounded transition-colors"
              aria-label="Close chat"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  <MessageCircle size={48} className="mx-auto mb-4 text-gray-300" />
                  <p>Hi! I'm here to help you file your motion.</p>
                  <p className="text-sm mt-2">Ask me anything about California family court filings.</p>
                </div>
              )}

              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}

              {isTyping && <TypingIndicator />}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Replies */}
            {latestQuickReplies.length > 0 && (
              <QuickReplies
                replies={latestQuickReplies}
                onReplyClick={handleQuickReply}
              />
            )}

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={connectionStatus === 'connected' ? 'Type your message...' : 'Connecting...'}
                  disabled={connectionStatus !== 'connected'}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || connectionStatus !== 'connected'}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors disabled:cursor-not-allowed"
                  aria-label="Send message"
                >
                  <Send size={20} />
                </button>
              </div>
            </div>

            {/* Session Info (Development) */}
            {process.env.NODE_ENV === 'development' && session && (
              <div className="text-xs text-gray-500 px-4 pb-2">
                Session: {session.id.substring(0, 8)}... | State: {session.state}
                {session.intent && ` | Intent: ${session.intent}`}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;