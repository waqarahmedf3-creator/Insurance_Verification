import React from 'react'

export interface ChatToggleProps {
  isOpen: boolean
  onToggle: () => void
  unreadCount?: number
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}

export const ChatToggle: React.FC<ChatToggleProps> = ({ 
  isOpen, 
  onToggle, 
  unreadCount = 0, 
  position = 'bottom-right' 
}) => {
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  return (
    <button
      onClick={onToggle}
      className={`chat-toggle ${positionClasses[position]} ${isOpen ? 'active' : ''}`}
      aria-label={isOpen ? 'Close chat' : 'Open chat'}
    >
      {isOpen ? (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 6L6 18M6 6L18 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ) : (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M6 9H18M6 13H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
      {unreadCount > 0 && !isOpen && (
        <span className="unread-badge">{unreadCount}</span>
      )}
    </button>
  )
}