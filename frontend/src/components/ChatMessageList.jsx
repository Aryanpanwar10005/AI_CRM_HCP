import React from 'react';
import TypingIndicator from './TypingIndicator';

const ChatMessageList = ({ messages, isTyping, chatEndRef }) => {
  return (
    <div className="conversation-area">
      {messages.map((msg, idx) => (
        <div key={idx} className={`message-bubble ${msg.role === 'user' ? 'user-msg' : 'assistant-msg'}`}>
          <span className="message-label">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
          <div className="message-content">{msg.content}</div>
        </div>
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={chatEndRef} />
    </div>
  );
};

export default ChatMessageList;
