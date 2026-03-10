import React, { useState, useRef } from 'react';
import { Send, Loader2, Paperclip, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from './Message';

const ChatInput = ({ onSend, onUpload, isLoading, isUploading }) => {
  const [input, setInput] = useState('');
  const [previews, setPreviews] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles);
      clearFiles();
      return;
    }
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

  const handleFileSelect = (e) => {
    const newFiles = Array.from(e.target.files || []);
    if (newFiles.length === 0) return;
    setSelectedFiles(prev => [...prev, ...newFiles]);
    setPreviews(prev => [...prev, ...newFiles.map(f => URL.createObjectURL(f))]);
    e.target.value = '';
  };

  const removeFile = (index) => {
    URL.revokeObjectURL(previews[index]);
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    previews.forEach(p => URL.revokeObjectURL(p));
    setPreviews([]);
    setSelectedFiles([]);
  };

  const busy = isLoading || isUploading;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2 sticky bottom-0 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
      {/* Image Previews */}
      {previews.length > 0 && (
        <div className="mb-2 flex items-start gap-2 px-2 flex-wrap">
          {previews.map((src, i) => (
            <div key={i} className="relative">
              <img src={src} alt={`Preview ${i + 1}`} className="w-20 h-20 object-cover rounded-xl border border-slate-600/50" />
              <button
                onClick={() => removeFile(i)}
                className="absolute -top-1.5 -right-1.5 bg-slate-700 border border-slate-600 rounded-full p-0.5 text-slate-300 hover:text-white hover:bg-red-600 transition-colors"
              >
                <X size={12} />
              </button>
            </div>
          ))}
          <span className="text-xs text-slate-400 mt-1 self-end">
            {previews.length} prescription image{previews.length > 1 ? 's' : ''} ready to upload
          </span>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="relative flex items-end gap-2 w-full bg-slate-800/60 backdrop-blur-xl border border-slate-600/50 rounded-3xl shadow-xl transition-all focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20"
      >
        {/* Attachment Button */}
        <div className="p-2 shrink-0">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
            className={cn(
              "flex items-center justify-center rounded-full p-2.5 transition-colors duration-200",
              busy
                ? "text-slate-500 cursor-not-allowed"
                : "text-slate-400 hover:text-blue-300 hover:bg-slate-700/50 cursor-pointer"
            )}
            title="Upload prescription image"
          >
            <Paperclip size={18} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedFiles.length > 0 ? "Press Enter to analyze prescription..." : "Ask a health-related question..."}
          className="w-full bg-transparent text-slate-100 placeholder:text-slate-400 p-4 pl-0 min-h-[56px] max-h-48 resize-none focus:outline-none scrollbar-hide"
          rows={1}
          disabled={busy}
        />

        <div className="p-2 shrink-0">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={(!input.trim() && selectedFiles.length === 0) || busy}
            className={cn(
              "flex items-center justify-center rounded-full p-3 transition-colors duration-200 shadow-md",
              (input.trim() || selectedFiles.length > 0) && !busy
                ? "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/40 cursor-pointer"
                : "bg-slate-700/50 text-slate-500 cursor-not-allowed border border-slate-600/30"
            )}
          >
            {busy ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} className="ml-0.5" />}
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
