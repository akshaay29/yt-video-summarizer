import React, { useState } from 'react';
import { Copy, CheckCircle } from 'lucide-react';


const SummaryCard = ({ summary }) => {
  const [copied, setCopied] = useState(false);

  if (!summary) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full max-w-2xl mx-auto glass-panel p-6 md:p-8 animate-slide-down mb-8">
      <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-800">
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500">
          AI Summary
        </h2>
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 text-sm bg-gray-800/50 hover:bg-gray-700/50 px-3 py-1.5 rounded-lg border border-gray-700"
        >
          {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
          {copied ? 'Copied!' : 'Copy Text'}
        </button>
      </div>
      
      <div className="prose prose-invert max-w-none text-gray-300 leading-relaxed whitespace-pre-wrap">
        {summary}
      </div>
    </div>
  );
};

export default SummaryCard;
