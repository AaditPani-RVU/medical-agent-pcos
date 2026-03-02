import React from 'react';
import { Bot, User, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const Message = ({ role, content, sources = [] }) => {
  const isUser = role === 'user';

  // Basic styling for the markdown returned by the backend
  const formattedContent = content.split('\n').map((line, i) => {
    if (line.startsWith('### ')) {
      return <h3 key={i} className="text-lg font-semibold text-blue-300 mt-4 mb-2">{line.replace('### ', '')}</h3>;
    }
    if (line.trim() === '') {
      return <div key={i} className="h-2" />;
    }
    // Bold text handling
    const boldRegex = /\*\*(.*?)\*\*/g;
    if (boldRegex.test(line)) {
      const parts = line.split(boldRegex);
      return (
        <p key={i} className="mb-1 leading-relaxed text-slate-200">
          {parts.map((part, index) => 
            index % 2 === 1 ? <strong key={index} className="text-white font-medium">{part}</strong> : part
          )}
        </p>
      );
    }
    return <p key={i} className="mb-1 leading-relaxed text-slate-200">{line}</p>;
  });

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "flex w-full gap-4 p-4 md:p-6 mb-4 rounded-2xl max-w-4xl mx-auto",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md border",
        isUser 
          ? "bg-blue-600/20 border-blue-500/50 text-blue-400" 
          : "bg-emerald-600/20 border-emerald-500/50 text-emerald-400"
      )}>
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>

      {/* Bubble */}
      <div className={cn(
        "flex flex-col gap-2 max-w-[85%] sm:max-w-[75%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-5 py-4 rounded-2xl shadow-sm border glass-panel",
          isUser 
            ? "bg-blue-900/30 border-blue-700/40 rounded-tr-sm" 
            : "bg-slate-800/40 border-slate-700/50 rounded-tl-sm"
        )}>
          <div className="text-sm md:text-base">
            {formattedContent}
          </div>
        </div>
        
        {/* Sources */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-2 flex flex-col gap-2 w-full">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">Verified Sources</h4>
            <div className="flex flex-wrap gap-2">
              {sources.map((url, idx) => (
                <a 
                  key={idx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/60 border border-slate-700/60 rounded-full text-xs text-blue-300 hover:text-blue-200 hover:bg-slate-700/80 hover:border-blue-500/50 transition-all duration-200 shadow-sm"
                  title={url}
                >
                  <ExternalLink size={12} />
                  <span className="truncate max-w-[150px]">
                    {new URL(url).hostname.replace('www.', '')}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Message;
