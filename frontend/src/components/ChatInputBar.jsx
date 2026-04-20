import React from 'react';
import { Loader2 } from 'lucide-react';

const ChatInputBar = ({ value, onChange, onSubmit, isTyping }) => {
  return (
    <form className="chat-input-row" onSubmit={onSubmit}>
      <input
        type="text"
        placeholder="Describe interaction..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={isTyping}
      />
      <button type="submit" className="log-btn" disabled={isTyping || !value.trim()}>
        <span className="ai-icon-circle">
          {isTyping ? <Loader2 className="animate-spin" size={12} /> : 'A'}
        </span>
        Log
      </button>
    </form>
  );
};

export default ChatInputBar;
