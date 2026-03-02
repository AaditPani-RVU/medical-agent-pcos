import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from './Message';

const ChatInput = ({ onSend, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2 sticky bottom-0 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
      <form 
        onSubmit={handleSubmit}
        className="relative flex items-end gap-2 w-full bg-slate-800/60 backdrop-blur-xl border border-slate-600/50 rounded-3xl shadow-xl transition-all focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a health-related question..."
          className="w-full bg-transparent text-slate-100 placeholder:text-slate-400 p-4 pl-6 min-h-[56px] max-h-48 resize-none focus:outline-none scrollbar-hide"
          rows={1}
          disabled={isLoading}
        />
        
        <div className="p-2 shrink-0">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              "flex items-center justify-center rounded-full p-3 transition-colors duration-200 shadow-md",
              input.trim() && !isLoading
                ? "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/40 cursor-pointer"
                : "bg-slate-700/50 text-slate-500 cursor-not-allowed border border-slate-600/30"
            )}
          >
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} className="ml-0.5" />}
          </motion.button>
        </div>
      </form>
      <div className="text-center mt-2 px-4 flex justify-center w-full">
         <span className="text-[10px] text-slate-500 max-w-lg leading-tight">
          This AI assistant uses trusted medical sources but cannot provide a diagnosis. Always consult a healthcare professional for medical advice.
         </span>
      </div>
    </div>
  );
};

export default ChatInput;
