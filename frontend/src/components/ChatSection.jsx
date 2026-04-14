import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const ChatSection = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'ai', content: "Hi! I've analyzed the video. What would you like to know?" }
  ]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    setInput('');
    
    // Add user message to UI
    const newMessages = [...messages, { role: 'user', content: userQuery }];
    setMessages(newMessages);

    try {
      // Temporary "typing..." state
      setMessages([...newMessages, { role: 'ai', content: '...', isTyping: true }]);
      
      const response = await onSendMessage(userQuery);
      
      // Update with real response
      setMessages([...newMessages, { role: 'ai', content: response }]);
    } catch (error) {
      setMessages([
        ...newMessages, 
        { role: 'ai', content: "Sorry, I had trouble finding that answer or connecting to the server.", isError: true }
      ]);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto glass-panel flex flex-col h-[500px] overflow-hidden animate-slide-down shadow-2xl">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 bg-gray-900/80 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-white">Chat with Video</h3>
          <p className="text-xs text-green-400 font-medium tracking-wide">RAG PIPELINE ACTIVE</p>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            <div className={`flex max-w-[85%] gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              
              {/* Avatar */}
              <div className="flex-shrink-0 mt-1">
                {msg.role === 'user' ? (
                  <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                    <User className="w-5 h-5 text-gray-300" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>

              {/* Bubble */}
              <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                {msg.isTyping ? (
                  <div className="flex gap-1 items-center h-6 px-1">
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                ) : (
                  <p className={`text-[15px] leading-relaxed ${msg.isError ? 'text-red-400' : 'text-gray-100'}`}>
                    {msg.content}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/80">
        <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about the video..."
            className="input-field pr-12 focus:ring-1 transition-shadow"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2 rounded-xl bg-purple-600/20 text-purple-400 hover:bg-purple-600 hover:text-white disabled:opacity-50 disabled:hover:bg-purple-600/20 disabled:hover:text-purple-400 transition-all"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatSection;
