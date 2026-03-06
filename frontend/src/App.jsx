import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity } from 'lucide-react';
import Message from './components/Message';
import ChatInput from './components/ChatInput';

const App = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your healthcare information assistant. How can I help you and your family today?\n\n*Note: I provide reliable information from trusted medical sources but cannot diagnose or prescribe treatments.*' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (query) => {
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Filter out the initial welcome message from the history to save tokens
      const history = messages.filter(msg => !msg.content.includes("Hello! I am your healthcare information assistant"));
      
      const response = await axios.post('http://localhost:8000/api/chat', { 
        query,
        history
      });
      
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error fetching chat response:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I apologize, but I encountered an error connecting to the server. Please ensure the backend is running.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Background Decorative Elements */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Header */}
      <header className="flex-shrink-0 w-full glass z-10 sticky top-0 px-6 py-4 flex items-center justify-center gap-3">
        <div className="bg-blue-600/20 p-2 rounded-xl text-blue-400 border border-blue-500/30">
          <Activity size={24} />
        </div>
        <div>
          <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-100 to-blue-300 bg-clip-text text-transparent">Health Info Assistant</h1>
          <p className="text-xs text-blue-200/60 font-medium tracking-wide">TRUSTED CLINICAL SOURCES</p>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto w-full mx-auto px-2 md:px-0 py-6 scrollbar-hide relative z-10 flex flex-col">
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <Message key={idx} role={msg.role} content={msg.content} sources={msg.sources} />
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex w-full gap-4 p-4 md:p-6 mb-4 rounded-2xl max-w-4xl mx-auto flex-row items-center"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-slate-800 border border-slate-700 text-slate-400">
              <Activity size={20} className="animate-pulse-slow" />
            </div>
            <div className="h-10 px-5 flex items-center justify-center gap-1.5 glass-panel rounded-full relative overflow-hidden">
               <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0 }} className="w-1.5 h-1.5 bg-blue-400 rounded-full block" />
               <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.2 }} className="w-1.5 h-1.5 bg-blue-400 rounded-full block" />
               <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.4 }} className="w-1.5 h-1.5 bg-blue-400 rounded-full block" />
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} className="h-20" /> {/* Spacer */}
      </main>

      {/* Input Area */}
      <div className="flex-shrink-0 w-full relative z-20 pb-4">
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default App;
