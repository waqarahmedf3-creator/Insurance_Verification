import React from 'react'

export interface ChatMessageProps {
  role: 'user' | 'bot'
  text: string
  timestamp?: Date
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, text, timestamp = new Date() }) => {
  const isUser = role === 'user'
  
  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-header">
        <span className="message-role">{isUser ? 'You' : 'AI Assistant'}</span>
        <span className="message-time">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      <div className="message-content">
        {text.split('\n').map((line, index) => (
          <p key={index} className="message-line">{line}</p>
        ))}
      </div>
    </div>
  )
}