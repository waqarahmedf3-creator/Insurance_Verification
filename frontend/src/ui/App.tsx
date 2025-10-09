import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { VerifyForm } from './VerifyForm'
import { PolicyManagement } from './PolicyManagement'
import { Chatbot } from './Chatbot'

const Navbar: React.FC = () => {
  const location = useLocation()
  
  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand">
          <span className="nav-logo">🏥</span>
          <h1 className="nav-title">Insurance Verification</h1>
          <span className="nav-badge">Insurance Portal</span>
        </div>
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Verification Form
          </Link>
          <Link 
            to="/policies" 
            className={`nav-link ${location.pathname === '/policies' ? 'active' : ''}`}
          >
            Policy Management
          </Link>
        </div>
      </div>
    </nav>
  )
}

const HomePage: React.FC = () => {
  return (
    <div className="container">
      <div className="grid grid-1">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="title">Verify Coverage</div>
              <div className="subtitle">Check status, policy and expiry</div>
            </div>
          </div>
          <div className="card-body">
            <VerifyForm />
          </div>
        </div>
      </div>
    </div>
  )
}

const PoliciesPage: React.FC = () => {
  return (
    <div className="container">
      <PolicyManagement />
    </div>
  )
}

export const App: React.FC = () => {
  const [isChatbotOpen, setIsChatbotOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  const handleChatbotToggle = () => {
    setIsChatbotOpen(!isChatbotOpen)
    if (!isChatbotOpen) {
      setUnreadCount(0) // Reset unread count when opening
    }
  }

  const handleNewMessage = () => {
    if (!isChatbotOpen) {
      setUnreadCount(prev => prev + 1)
    }
  }

  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/policies" element={<PoliciesPage />} />
          </Routes>
        </main>
        
        {/* Floating Chatbot Toggle */}
        {!isChatbotOpen && (
          <button
            onClick={handleChatbotToggle}
            className="chatbot-toggle"
            aria-label="Open chatbot"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            {unreadCount > 0 && (
              <span className="chatbot-notification-badge">{unreadCount}</span>
            )}
          </button>
        )}

        {/* Chatbot Panel */}
        {isChatbotOpen && (
          <div className="chatbot-panel">
            <div className="chatbot-header">
              <div className="chatbot-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <div>
                  <h3>Insurance Assistant</h3>
                  <p>Powered by Google Gemini</p>
                </div>
              </div>
              <button
                onClick={handleChatbotToggle}
                className="chatbot-close"
                aria-label="Close chatbot"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div className="chatbot-body">
              <Chatbot onNewMessage={handleNewMessage} />
            </div>
          </div>
        )}
      </div>
    </Router>
  )
}


