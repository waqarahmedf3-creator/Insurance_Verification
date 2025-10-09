import React, { useState, useRef, useEffect } from 'react'
import { ChatMessage, ChatMessageProps } from './ChatMessage'

export interface ChatPanelProps {
  messages: ChatMessageProps[]
  isLoading?: boolean
  onSendMessage: (message: string) => void
  placeholder?: string
  disabled?: boolean
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ 
  messages, 
  isLoading = false, 
  onSendMessage, 
  placeholder = "Type your message...",
  disabled = false
}) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  useEffect(() => {
    if (!disabled && !isLoading) {
      inputRef.current?.focus()
    }
  }, [disabled, isLoading])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || disabled || isLoading) return
    
    onSendMessage(trimmed)
    setInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <ChatMessage key={index} {...message} />
        ))}
        {isLoading && (
          <div className="chat-message bot-message">
            <div className="message-header">
              <span className="message-role">AI Assistant</span>
              <span className="message-time">Now</span>
            </div>
            <div className="message-content">
              <div className="loading-indicator">
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-panel">
        <div className="chat-input-container">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="chat-input"
          />
          <button
            onClick={handleSend}
            disabled={disabled || isLoading || !input.trim()}
            className="chat-send-btn"
          >
            {isLoading ? (
              <span className="loading-spinner"></span>
            ) : (
              'Send'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}