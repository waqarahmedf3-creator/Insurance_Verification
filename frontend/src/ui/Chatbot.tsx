import React, { useState, useEffect, useRef } from 'react'
import { GoogleGenerativeAI } from '@google/generative-ai'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const AUTH = 'Bearer dev-secret'
const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY

interface ChatbotProps {
  onNewMessage?: () => void
}

export const Chatbot: React.FC<ChatbotProps> = ({ onNewMessage }) => {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{role:'user'|'bot', text:string, timestamp?: Date}>>([
    { 
      role: 'bot', 
      text: 'Hello! I\'m your AI insurance assistant. I can help you understand your policy coverage, check verification status, explain insurance terms, and answer any insurance-related questions. How can I assist you today?',
      timestamp: new Date()
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Suggested prompts for quick actions
  const suggestedPrompts = [
    "What does my policy cover?",
    "How do I verify my insurance?",
    "Explain deductibles",
    "What's a premium?"
  ]

  // Initialize Gemini AI
  const genAI = GEMINI_API_KEY ? new GoogleGenerativeAI(GEMINI_API_KEY) : null
  const model = genAI?.getGenerativeModel({ model: 'gemini-2.5-flash' })

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Notify parent component of new messages
  useEffect(() => {
    if (messages.length > 1) { // Don't notify for initial message
      onNewMessage?.()
    }
  }, [messages])

  // Function to detect 6-digit policy numbers in user messages
  const detectPolicyNumber = (message: string): string | null => {
    const sixDigitPattern = /\b\d{6}\b/g;
    const matches = message.match(sixDigitPattern);
    return matches ? matches[0] : null;
  };

  // Function to lookup policy by number
  const lookupPolicyByNumber = async (policyNumber: string) => {
    try {
      console.log(`Looking up policy number: ${policyNumber}`);
      const response = await fetch(`${API_BASE}/api/policy-info/by-number?policyNumber=${policyNumber}`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': AUTH 
        }
      });
      
      if (response.status === 404) {
        return { error: 'Policy not found', status: 404 };
      }
      
      if (!response.ok) {
        throw new Error(`Policy lookup failed: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Policy lookup successful:', data);
      return data;
    } catch (error) {
      console.error('Policy lookup error:', error);
      return { error: (error as Error).message || 'Failed to lookup policy', status: 500 };
    }
  };

  const sendMessageToGemini = async (message: string, conversationHistory: Array<{role:string, text:string}>) => {
    if (!GEMINI_API_KEY) throw new Error('Gemini API key not available')
    
    try {
      // Try using the SDK first
      if (model) {
        const context = conversationHistory.map(msg => `${msg.role}: ${msg.text}`).join('\n')
        const prompt = `You are a helpful insurance assistant. Based on the conversation history:\n${context}\n\nUser: ${message}\nAssistant: `
        
        console.log('Sending to Gemini SDK:', { message, contextLength: context.length })
        const result = await model.generateContent(prompt)
        const response = result.response.text()
        console.log('Gemini SDK response received:', response.substring(0, 100) + '...')
        return response
      } else {
        // Fallback to direct REST API call
        console.log('Using Gemini REST API fallback')
        return await sendMessageToGeminiREST(message, conversationHistory)
      }
    } catch (error) {
      console.error('Gemini SDK Error:', error)
      // Fallback to REST API
      return await sendMessageToGeminiREST(message, conversationHistory)
    }
  }

  const sendMessageToGeminiREST = async (message: string, conversationHistory: Array<{role:string, text:string}>) => {
    if (!GEMINI_API_KEY) throw new Error('Gemini API key not available')
    
    try {
      const context = conversationHistory.map(msg => `${msg.role}: ${msg.text}`).join('\n')
      const prompt = `You are a helpful insurance assistant. Based on the conversation history:\n${context}\n\nUser: ${message}\nAssistant: `
      
      console.log('Sending to Gemini REST API:', { message, contextLength: context.length })
      
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contents: [{
              parts: [{ text: prompt }]
            }]
          })
        }
      )
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(`Gemini API error: ${response.status} - ${errorData.error?.message || response.statusText}`)
      }
      
      const data = await response.json()
      const generatedText = data.candidates?.[0]?.content?.parts?.[0]?.text
      
      if (!generatedText) {
        throw new Error('No response text generated')
      }
      
      console.log('Gemini REST API response received:', generatedText.substring(0, 100) + '...')
      return generatedText
    } catch (error) {
      console.error('Gemini REST API Error:', error)
      if (error instanceof Error && error.message?.includes('404')) {
        throw new Error('Gemini API endpoint not found. The model or endpoint may be incorrect.')
      } else if ((error as Error).message?.includes('API key')) {
        throw new Error('Invalid API key or authentication error.')
      } else {
        throw new Error(`Gemini API error: ${(error as Error).message || 'Unknown error'}`)
      }
    }
  }

  const getPolicyContext = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/policy-info`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': AUTH 
        },
        body: JSON.stringify({ 
          member_id: '1234567890', 
          dob: '1990-01-01', 
          last_name: 'Doe' 
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch policy data')
      }
      
      return await response.json()
    } catch (error) {
      console.error('Policy fetch error:', error)
      return null
    }
  }

  const sendMessage = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    
    setIsLoading(true)
    setIsTyping(true)
    setMessages(m => [...m, { role: 'user', text: trimmed, timestamp: new Date() }])
    setInput('')

    try {
      let reply: string
      let enrichedPrompt = trimmed;
      let policyContext = '';

      // Step 1: Detect 6-digit policy numbers in user message
      const detectedPolicyNumber = detectPolicyNumber(trimmed);
      let policyData = null;

      if (detectedPolicyNumber) {
        console.log(`Detected policy number: ${detectedPolicyNumber}`);
        policyData = await lookupPolicyByNumber(detectedPolicyNumber);
        
        if (policyData && !policyData.error) {
          // Format policy data for Gemini system prompt as specified
          policyContext = `Real policy data for ${detectedPolicyNumber}:
- Status: ${policyData.coverage_status || 'Unknown'}
- Type: ${policyData.plan_type || 'Health Insurance Premium'}
- Provider: ${policyData.provider_name || 'Unknown Provider'}
- Coverage: ${policyData.coverage_amount || 'Not specified'}
- Premium: ${policyData.premium_status || 'Unknown'}
- Expiry: ${policyData.expiry_date || 'Not specified'}
- Member: ${policyData.member_name || 'Unknown Member'}

Use this actual data to answer the user's question accurately.`;
        } else if (policyData && policyData.error) {
          // Policy not found or error occurred
          policyContext = `Policy ${detectedPolicyNumber} was not found in our records. Inform the user that the policy number is not recognized and ask them to verify it.`;
        }
      }

      // Step 2: Check for insurance-related keywords if no policy detected
      if (!detectedPolicyNumber && /cover|valid|expire|policy|benefit|claim/i.test(trimmed)) {
        policyData = await getPolicyContext();
        if (policyData) {
          policyContext = `Policy Information: Policy ${policyData.policy_number}, Status: ${policyData.coverage_status}, Expires: ${policyData.expiry_date}. Provider: ${policyData.provider_name}`;
        }
      }

      // Step 3: Send to Gemini with enriched context
      if (model) {
        const conversationHistory = messages.map(msg => ({ role: msg.role, text: msg.text }));
        
        if (policyContext) {
          // Use enriched prompt with policy data
          enrichedPrompt = `${policyContext}\n\nUser question: ${trimmed}`;
        }
        
        reply = await sendMessageToGemini(enrichedPrompt, conversationHistory);
      } else {
        // Fallback without AI
        if (policyData && !policyData.error) {
          reply = `Policy ${detectedPolicyNumber}: Status ${policyData.coverage_status}, Coverage ${policyData.coverage_amount}, Expires ${policyData.expiry_date}`;
        } else if (policyData && policyData.error) {
          reply = `I couldn't find policy ${detectedPolicyNumber}. Please verify the policy number and try again.`;
        } else {
          reply = "I'm here to help with insurance-related questions. Please ask about coverage, policies, claims, or other insurance topics.";
        }
      }

      setIsTyping(false)
      setMessages(m => [...m, { role: 'bot', text: reply, timestamp: new Date() }])
    } catch (error) {
      console.error('Chat error:', error)
      setIsTyping(false)
      let errorMessage = 'I apologize, but I encountered an error processing your request. '
      
      if (error instanceof Error && error.message?.includes('Gemini')) {
        errorMessage += `AI service error: ${error.message}. Using fallback responses. `
      } else {
        errorMessage += 'Please try again. '
      }
      
      // Provide helpful fallback response based on user intent
      const detectedPolicyNumber = detectPolicyNumber(trimmed)
      if (detectedPolicyNumber) {


        const detectedPolicyNumber = detectPolicyNumber(trimmed)
        errorMessage += `For policy ${detectedPolicyNumber} questions, please verify the policy number or provide your member ID for manual lookup.`

      } else if (/cover|valid|expire|policy|benefit|claim/i.test(input.trim())) {
        errorMessage += 'For policy-related questions, please provide your member ID and I can help you check your coverage status.'
      } else {
        errorMessage += 'I can help with insurance questions, policy verification, and general insurance information.'
      }
      
      setMessages(m => [...m, { role: 'bot', text: errorMessage }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleSuggestedPrompt = (prompt: string) => {
    setInput(prompt)
    setTimeout(() => {
      sendMessage()
    }, 100)
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-messages">
        {messages.map((message, index) => (
          <div key={index} className={`chatbot-message ${message.role}`}>
            <div className="chatbot-message-content">
              <div className="chatbot-message-header">
                <span className="chatbot-message-role">
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </span>
                {message.timestamp && (
                  <span className="chatbot-message-time">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
              <div className="chatbot-message-text">{message.text}</div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="chatbot-message bot typing">
            <div className="chatbot-message-content">
              <div className="chatbot-message-header">
                <span className="chatbot-message-role">AI Assistant</span>
              </div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length === 1 && (
        <div className="chatbot-suggestions">
          {suggestedPrompts.map((prompt, index) => (
            <button
              key={index}
              className="chatbot-suggestion"
              onClick={() => handleSuggestedPrompt(prompt)}
              disabled={isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      <div className="chatbot-input-area">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your policy, coverage, claims..."
          disabled={isLoading}
          className="chatbot-textarea"
          rows={1}
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
          className="chatbot-send-button"
        >
          {isLoading ? (
            <div className="loading-spinner"></div>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22,2 15,22 11,13 2,9"></polygon>
            </svg>
          )}
        </button>
      </div>

      {!GEMINI_API_KEY && (
        <div className="chatbot-fallback-notice">
          AI responses in fallback mode. Configure Gemini API key for enhanced responses.
        </div>
      )}
    </div>
  )
}


