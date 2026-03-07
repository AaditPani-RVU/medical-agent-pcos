import React, { useState, useRef } from 'react';
import { Send, Loader2, Paperclip, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from './Message';

const ChatInput = ({ onSend, onUpload, isLoading, isUploading }) => {
  const [input, setInput] = useState('');
  const [preview, setPreview] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedFile) {
      onUpload(selectedFile);
      clearFile();
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
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
    e.target.value = '';
  };

  const clearFile = () => {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setSelectedFile(null);
  };

  const busy = isLoading || isUploading;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2 sticky bottom-0 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
      {/* Image Preview */}
      {preview && (
        <div className="mb-2 flex items-start gap-2 px-2">
          <div className="relative">
            <img src={preview} alt="Preview" className="w-20 h-20 object-cover rounded-xl border border-slate-600/50" />
            <button
              onClick={clearFile}
              className="absolute -top-1.5 -right-1.5 bg-slate-700 border border-slate-600 rounded-full p-0.5 text-slate-300 hover:text-white hover:bg-red-600 transition-colors"
            >
              <X size={12} />
            </button>
          </div>
          <span className="text-xs text-slate-400 mt-1">Prescription image ready to upload</span>
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
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedFile ? "Press Enter to analyze prescription..." : "Ask a health-related question..."}
          className="w-full bg-transparent text-slate-100 placeholder:text-slate-400 p-4 pl-0 min-h-[56px] max-h-48 resize-none focus:outline-none scrollbar-hide"
          rows={1}
          disabled={busy}
        />

        <div className="p-2 shrink-0">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={(!input.trim() && !selectedFile) || busy}
            className={cn(
              "flex items-center justify-center rounded-full p-3 transition-colors duration-200 shadow-md",
              (input.trim() || selectedFile) && !busy
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
