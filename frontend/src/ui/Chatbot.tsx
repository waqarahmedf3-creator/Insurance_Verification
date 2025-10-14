import React, { useState, useEffect, useRef } from 'react'
import { GoogleGenerativeAI } from '@google/generative-ai'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
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
  const [isCreatingPolicy, setIsCreatingPolicy] = useState(false)
  const [createStepIndex, setCreateStepIndex] = useState(0)
  const [policyDraft, setPolicyDraft] = useState<any>({
    policy_number: '',
    provider: '',
    first_name: '',
    last_name: '',
    dob: '',
    coverage_amount: '',
    premium_amount: '',
    expiry_date: ''
  })
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

  // Helper: intent checks
  const isCountPoliciesIntent = (message: string) => /\b(how many|count|number)\b.*\b(policies|saved policies)\b/i.test(message)
  const isAddPolicyIntent = (message: string) => /(add|create)\b.*\b(policy|new policy)/i.test(message)

  // Creation steps configuration
  const creationSteps: Array<{ key: keyof typeof policyDraft, prompt: string, validate?: (val: string) => string | null, transform?: (val: string) => any }> = [
    { key: 'policy_number', prompt: "What's the Policy Number?", validate: (v) => v.trim().length >= 6 ? null : 'Policy number must be at least 6 characters.' },
    { key: 'provider', prompt: 'Provider Name?', validate: (v) => v.trim() ? null : 'Provider is required.' },
    { key: 'first_name', prompt: 'Member First Name?', validate: (v) => v.trim() ? null : 'First name is required.' },
    { key: 'last_name', prompt: 'Member Last Name?', validate: (v) => v.trim() ? null : 'Last name is required.' },
    { key: 'dob', prompt: 'Date of Birth (YYYY-MM-DD)?', validate: (v) => {
        const ok = /^\d{4}-\d{2}-\d{2}$/.test(v.trim())
        if (!ok) return 'DOB must be YYYY-MM-DD.'
        const d = new Date(v)
        if (isNaN(d.getTime())) return 'Invalid DOB date.'
        if (d > new Date()) return 'DOB cannot be in the future.'
        return null
      }
    },
    { key: 'coverage_amount', prompt: 'Coverage Amount (numeric, > 0)?', validate: (v) => {
        const n = Number(v)
        return n > 0 ? null : 'Coverage amount must be a positive number.'
      }, transform: (v) => Number(v)
    },
    { key: 'premium_amount', prompt: 'Premium Amount (numeric, > 0)?', validate: (v) => {
        const n = Number(v)
        return n > 0 ? null : 'Premium amount must be a positive number.'
      }, transform: (v) => Number(v)
    },
    { key: 'expiry_date', prompt: 'Expiry Date (YYYY-MM-DD, must be future)?', validate: (v) => {
        const ok = /^\d{4}-\d{2}-\d{2}$/.test(v.trim())
        if (!ok) return 'Expiry date must be YYYY-MM-DD.'
        const d = new Date(v)
        if (isNaN(d.getTime())) return 'Invalid expiry date.'
        const today = new Date(); today.setHours(0,0,0,0)
        if (d <= today) return 'Expiry date must be in the future.'
        return null
      }
    }
  ]

  const startPolicyCreation = () => {
    setIsCreatingPolicy(true)
    setCreateStepIndex(0)
    setPolicyDraft({
      policy_number: '', provider: '', first_name: '', last_name: '', dob: '', coverage_amount: '', premium_amount: '', expiry_date: ''
    })
    const firstPrompt = creationSteps[0].prompt
    setMessages(m => [...m, { role: 'bot', text: `Let’s add a new policy. ${firstPrompt}`, timestamp: new Date() }])
  }

  const askNextStep = (nextIndex: number) => {
    const nextPrompt = creationSteps[nextIndex]?.prompt
    if (nextPrompt) {
      setMessages(m => [...m, { role: 'bot', text: nextPrompt, timestamp: new Date() }])
    }
  }

  const completePolicyCreation = async () => {
    // Generate a Member ID automatically to align with backend requirements
    const generatedMemberId = Math.floor(100000000 + Math.random()*900000000).toString()
    const payload = {
      provider: policyDraft.provider,
      member_id: generatedMemberId,
      policy_number: policyDraft.policy_number,
      first_name: policyDraft.first_name,
      last_name: policyDraft.last_name,
      dob: policyDraft.dob,
      coverage_amount: policyDraft.coverage_amount,
      premium_amount: policyDraft.premium_amount,
      expiry_date: policyDraft.expiry_date
    }
    try {
      const resp = await fetch(`${API_BASE}/api/policies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': AUTH },
        body: JSON.stringify(payload)
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to create policy')
      }
      const created = await resp.json()
      setMessages(m => [...m, { role: 'bot', text: `Policy ${created.policy_number} has been successfully added.`, timestamp: new Date() }])
    } catch (e) {
      setMessages(m => [...m, { role: 'bot', text: `Sorry, I couldn’t save the policy: ${(e as Error).message}`, timestamp: new Date() }])
    } finally {
      setIsCreatingPolicy(false)
      setCreateStepIndex(0)
      setPolicyDraft({ policy_number: '', provider: '', first_name: '', last_name: '', dob: '', coverage_amount: '', premium_amount: '', expiry_date: '' })
    }
  }

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

  // Unified saved policies access helpers
  const fetchSavedPolicyByNumber = async (policyNumber: string): Promise<any | null> => {
    try {
      const resp = await fetch(`${API_BASE}/api/policies/by-number?policyNumber=${encodeURIComponent(policyNumber)}`, {
        headers: { 'Authorization': AUTH }
      })
      if (!resp.ok) return null
      return await resp.json()
    } catch {
      return null
    }
  }

  const fetchSavedPoliciesByMember = async (firstName: string, lastName: string): Promise<any[]> => {
    try {
      const resp = await fetch(`${API_BASE}/api/policies/by-member?first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}`, {
        headers: { 'Authorization': AUTH }
      })
      if (!resp.ok) return []
      const data = await resp.json()
      return Array.isArray(data?.policies) ? data.policies : []
    } catch {
      return []
    }
  }

  const formatPolicyDetails = (p: any): string => {
    if (!p) return ''
    const lines = [
      `Policy Number: ${p.policy_number ?? '-'}`,
      `Provider: ${p.provider ?? p.provider_name ?? '-'}`,
      `Member: ${p.first_name ?? '-'} ${p.last_name ?? '-'}`,
      `DOB: ${p.dob ?? p.date_of_birth ?? '-'}`,
      `Coverage: ${p.coverage_amount ?? p.coverage ?? '-'}`,
      `Premium: ${p.premium_amount ?? p.premium ?? '-'}`,
      `Expiry: ${p.expiry_date ?? p.expiry ?? '-'}`,
      `Status: ${p.status ?? '-'}`,
    ]
    return lines.join('\n')
  }

  const detectMemberName = (text: string): { first: string; last: string } | null => {
    const patterns = [/for\s+([a-zA-Z]+)\s+([a-zA-Z]+)/i, /member\s+([a-zA-Z]+)\s+([a-zA-Z]+)/i]
    for (const re of patterns) {
      const m = re.exec(text)
      if (m && m[1] && m[2]) return { first: m[1], last: m[2] }
    }
    const words = text.trim().split(/\s+/)
    if (words.length >= 2) {
      const lastTwo = words.slice(-2)
      if (/^[A-Za-z]+$/.test(lastTwo[0]) && /^[A-Za-z]+$/.test(lastTwo[1])) {
        return { first: lastTwo[0], last: lastTwo[1] }
      }
    }
    return null
  }

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

  const sendMessage = async (providedMessage?: string) => {
    const rawInput = providedMessage ?? input
    const trimmed = rawInput.trim()
    if (!trimmed) return
    
    setIsLoading(true)
    setIsTyping(true)
    setMessages(m => [...m, { role: 'user', text: trimmed, timestamp: new Date() }])
    setInput('')

    try {
      // Intercept: Count saved policies
      if (!isCreatingPolicy && isCountPoliciesIntent(trimmed)) {
        try {
          const resp = await fetch(`${API_BASE}/api/policies`, { headers: { 'Authorization': AUTH } })
          if (!resp.ok) throw new Error(`Failed to fetch policies: ${resp.status}`)
          const data = await resp.json()
          const count = Array.isArray(data?.policies) ? data.policies.length : 0
          setIsTyping(false)
          setMessages(m => [...m, { role: 'bot', text: `There are currently ${count} saved policies in the system.`, timestamp: new Date() }])
          setIsLoading(false)
          return
        } catch (e) {
          setIsTyping(false)
          setMessages(m => [...m, { role: 'bot', text: `I couldn’t retrieve the saved policies count: ${(e as Error).message}`, timestamp: new Date() }])
          setIsLoading(false)
          return
        }
      }

      // Intercept: Start add policy flow
      if (!isCreatingPolicy && isAddPolicyIntent(trimmed)) {
        startPolicyCreation()
        setIsTyping(false)
        setIsLoading(false)
        return
      }

      // Continue add policy flow if active
      if (isCreatingPolicy) {
        const step = creationSteps[createStepIndex]
        if (!step) {
          // Safety: complete if steps exhausted
          await completePolicyCreation()
          setIsTyping(false)
          setIsLoading(false)
          return
        }
        const error = step.validate ? step.validate(trimmed) : null
        if (error) {
          setIsTyping(false)
          setMessages(m => [...m, { role: 'bot', text: `${error} Please try again.`, timestamp: new Date() }])
          // Re-ask same step
          askNextStep(createStepIndex)
          setIsLoading(false)
          return
        }
        const value = step.transform ? step.transform(trimmed) : trimmed
        setPolicyDraft((d: any) => ({ ...d, [step.key]: value }))
        const nextIndex = createStepIndex + 1
        setCreateStepIndex(nextIndex)
        if (nextIndex >= creationSteps.length) {
          await completePolicyCreation()
        } else {
          askNextStep(nextIndex)
        }
        setIsTyping(false)
        setIsLoading(false)
        return
      }
      let reply: string
      let enrichedPrompt = trimmed;
      let policyContext = '';

      // Step 1: Detect 6-digit policy numbers in user message
      const detectedPolicyNumber = detectPolicyNumber(trimmed);
      let policyData = null;

      if (detectedPolicyNumber) {
        console.log(`Detected policy number: ${detectedPolicyNumber}`);
        // Try unified saved policies first
        const saved = await fetchSavedPolicyByNumber(detectedPolicyNumber)
        if (saved) {
          const answerText = `Found saved policy.\n\n${formatPolicyDetails(saved)}`
          setIsTyping(false)
          setMessages(m => [...m, { role: 'bot', text: answerText, timestamp: new Date() }])
          setIsLoading(false)
          return
        }

        // Fallback to existing provider info lookup
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

      // Step 1b: Try member name search for saved policies
      const name = detectMemberName(trimmed)
      if (name) {
        const matches = await fetchSavedPoliciesByMember(name.first, name.last)
        if (matches.length > 0) {
          const details = matches.map((p: any) => formatPolicyDetails(p)).join('\n\n')
          const header = matches.length === 1 ? `Found 1 saved policy for ${name.first} ${name.last}.` : `Found ${matches.length} saved policies for ${name.first} ${name.last}.`
          const answerText = `${header}\n\n${details}`
          setIsTyping(false)
          setMessages(m => [...m, { role: 'bot', text: answerText, timestamp: new Date() }])
          setIsLoading(false)
          return
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

      } else if (/cover|valid|expire|policy|benefit|claim/i.test(trimmed)) {
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
    // Directly send the provided prompt to avoid race conditions with state updates
    sendMessage(prompt)
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


