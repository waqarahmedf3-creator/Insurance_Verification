import React, { useState } from 'react'
import Modal from './Modal'
import Toast from './Toast'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const AUTH = 'Bearer dev-secret'

export const VerifyForm: React.FC = () => {
  const [provider, setProvider] = useState('statelife')
  const [memberId, setMemberId] = useState('')
  const [dob, setDob] = useState('')
  const [lastName, setLastName] = useState('')
  const [result, setResult] = useState<any>(null)
  const [policy, setPolicy] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [showRenewForm, setShowRenewForm] = useState(false)
  const [renewLoading, setRenewLoading] = useState(false)
  const [renewMessage, setRenewMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [showSavedPolicies, setShowSavedPolicies] = useState(false)
  const [savedPolicies, setSavedPolicies] = useState<any[]>([])
  const [savedPoliciesLoading, setSavedPoliciesLoading] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<any>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false)
  const [policyToDelete, setPolicyToDelete] = useState<string | null>(null)

  // Renew/Add New Policy form state
  const [firstName, setFirstName] = useState('')
  const [renewLastName, setRenewLastName] = useState('')
  const [renewDob, setRenewDob] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [city, setCity] = useState('')
  const [stateProv, setStateProv] = useState('')
  const [zip, setZip] = useState('')
  const [policyType, setPolicyType] = useState('health')
  const [renewProvider, setRenewProvider] = useState('')
  const [renewMemberId, setRenewMemberId] = useState('')
  const [errorModalMessage, setErrorModalMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<{message: string, type: 'success' | 'error' | 'info' | 'warning'} | null>(null)

  const callVerify = async () => {
    console.log('callVerify: Starting verification...')
    if (!memberId || !dob || !lastName) {
      console.log('callVerify: Missing required fields')
      setErrorModalMessage("Please fill in all required fields: Member ID, Date of Birth, and Last Name")
      return
    }
    if (!/^\d{6}$/.test(memberId)) {
      console.log('callVerify: Invalid member ID format')
      setErrorModalMessage("Member ID must be exactly 6 numeric digits")
      return
    }
    
    console.log('callVerify: All validations passed, calling API...')
    setLoading(true)
    setResult(null)
    try {
      const requestBody = { provider, member_id: memberId, dob, last_name: lastName }
      console.log('callVerify: Request body:', JSON.stringify(requestBody, null, 2))
      
      const resp = await fetch(`${API_BASE}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': AUTH },
        body: JSON.stringify(requestBody)
      })
      console.log('callVerify: Response status:', resp.status)
      const data = await resp.json()
      console.log('callVerify: Response data:', JSON.stringify(data, null, 2))
      setResult(data)
    } catch (error) {
      console.error('callVerify: Error occurred:', error)
      setResult({
        error: true,
        message: "Unable to connect to verification service. Please try again later."
      })
    }
    setLoading(false)
  }

  const callPolicyInfo = async () => {
    if (!memberId) {
      setErrorModalMessage("Please enter a Member ID to retrieve policy information")
      return
    }
    if (!/^\d{6}$/.test(memberId)) {
      setErrorModalMessage("Member ID must be exactly 6 numeric digits")
      return
    }
    
    setLoading(true)
    setPolicy(null)
    setResult(null)
    
    try {
      const resp = await fetch(`${API_BASE}/api/policy-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': AUTH },
        body: JSON.stringify({ provider, member_id: memberId, dob, last_name: lastName })
      })
      
      if (!resp.ok) {
        let errorMessage = `HTTP error! status: ${resp.status}`
        try {
          const errorData = await resp.json()
          if (errorData.detail) {
            errorMessage = errorData.detail
          }
        } catch (e) {
          // If error response is not JSON, use default message
        }
        throw new Error(errorMessage)
      }
      
      const data = await resp.json()
      setPolicy(data)
    } catch (error) {
      setPolicy({
        error: true,
        message: "Unable to retrieve policy information. Please try again later.",
        details: error instanceof Error ? error.message : String(error)
      })
    }
    
    setLoading(false)
  }

  const clearAll = () => {
    setProvider('statelife')
    setMemberId('')
    setDob('')
    setLastName('')
    setResult(null)
    setPolicy(null)
    setRenewMessage(null)
  }

  const handleRenewMemberIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, ''); // Remove non-numeric characters
    if (value.length <= 6) {
      setRenewMemberId(value);
    }
  };

  const fetchSavedPolicies = async () => {
    setSavedPoliciesLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/policies`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || 'test-token'}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setSavedPolicies(data.policies || [])
      } else if (response.status === 401) {
        setErrorModalMessage('Authentication failed. Please log in again.')
        setSavedPolicies([])
      } else if (response.status === 404) {
        setSavedPolicies([]) // No policies found is not an error
      } else {
        const errorData = await response.json().catch(() => ({}))
        setErrorModalMessage(`Failed to fetch saved policies: ${errorData.detail || 'Server error'}`)
        setSavedPolicies([])
      }
    } catch (error) {
      console.error('Error fetching saved policies:', error)
      setErrorModalMessage('Network error: Unable to fetch saved policies. Please check your connection.')
      setSavedPolicies([])
    } finally {
      setSavedPoliciesLoading(false)
    }
  }

  const handleViewSavedPolicies = () => {
    setShowSavedPolicies(true)
    fetchSavedPolicies()
  }

  const handleEditPolicy = (policy: any) => {
    setEditingPolicy(policy)
    setShowEditModal(true)
  }

  const handleDeletePolicy = async (policyId: string) => {
    setPolicyToDelete(policyId)
    setShowDeleteConfirmModal(true)
  }

  const confirmDeletePolicy = async () => {
    if (!policyToDelete) return

    try {
      const response = await fetch(`${API_BASE}/api/policies/${policyToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || 'test-token'}`
        }
      })

      if (response.ok) {
        // Remove deleted policy from state
        setSavedPolicies(savedPolicies.filter(policy => policy.id !== policyToDelete))
        setSuccessMessage('Policy deleted successfully!')
        setToastMessage({message: 'Policy deleted successfully!', type: 'success'})
      } else if (response.status === 404) {
        setErrorModalMessage('Policy not found. It may have already been deleted.')
        // Remove from local state anyway since it's gone from server
        setSavedPolicies(savedPolicies.filter(policy => policy.id !== policyToDelete))
      } else if (response.status === 401) {
        setErrorModalMessage('Authentication failed. Please log in again.')
      } else {
        const errorData = await response.json().catch(() => ({}))
        setErrorModalMessage(`Failed to delete policy: ${errorData.detail || 'Server error'}`)
      }
    } catch (error) {
      console.error('Error deleting policy:', error)
      setErrorModalMessage('Network error: Unable to delete policy. Please check your connection.')
    } finally {
      setShowDeleteConfirmModal(false)
      setPolicyToDelete(null)
    }
  }

  const validateEditPolicy = () => {
    if (!editingPolicy) return "No policy data to validate"
    
    if (!editingPolicy.provider?.trim()) {
      return "Provider is required"
    }
    
    if (!editingPolicy.member_id?.trim()) {
      return "Member ID is required"
    }
    
    if (!/^\d{6}$/.test(editingPolicy.member_id)) {
      return "Member ID must be exactly 6 numeric digits"
    }
    
    if (editingPolicy.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editingPolicy.email)) {
      return "Please enter a valid email address"
    }
    
    if (editingPolicy.phone && !/^\+?[\d\s\-\(\)]+$/.test(editingPolicy.phone)) {
      return "Please enter a valid phone number"
    }
    
    if (editingPolicy.zip_code && !/^\d{5}(-\d{4})?$/.test(editingPolicy.zip_code)) {
      return "Please enter a valid ZIP code"
    }
    
    if (editingPolicy.coverage_amount && editingPolicy.coverage_amount < 0) {
      return "Coverage amount cannot be negative"
    }
    
    if (editingPolicy.premium_amount && editingPolicy.premium_amount < 0) {
      return "Premium amount cannot be negative"
    }
    
    return null
  }

  const handleUpdatePolicy = async () => {
    if (!editingPolicy) return

    // Validate form data
    const validationError = validateEditPolicy()
    if (validationError) {
      setErrorModalMessage(validationError)
      return
    }

    setRenewLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/policies/${editingPolicy.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || 'test-token'}`
        },
        body: JSON.stringify(editingPolicy)
      })

      if (response.ok) {
        const updatedPolicy = await response.json()
        // Update the policy in the saved policies list
        setSavedPolicies(savedPolicies.map(policy => 
          policy.id === updatedPolicy.id ? updatedPolicy : policy
        ))
        setShowEditModal(false)
        setEditingPolicy(null)
        setSuccessMessage('Policy updated successfully!')
        setToastMessage({message: 'Policy updated successfully!', type: 'success'})
      } else {
        const errorData = await response.json()
        setErrorModalMessage(`Failed to update policy: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error updating policy:', error)
      setErrorModalMessage('Error updating policy. Please try again.')
    } finally {
      setRenewLoading(false)
    }
  }

  const validateRenewForm = () => {
    if (!firstName.trim() || !renewLastName.trim() || !renewDob) return "First name, last name and DOB are required"
    if (!renewProvider || renewProvider.trim() === '') return "Provider is required"
    if (!renewMemberId || renewMemberId.trim() === '') return "Member ID is required"
    if (!/^\d{6}$/.test(renewMemberId)) return "Member ID must be exactly 6 digits"
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email address"
    if (phone && !/^\+?[0-9\-\s]{7,15}$/.test(phone)) return "Please enter a valid phone number"
    if (zip && !/^[0-9]{4,10}$/.test(zip)) return "Please enter a valid ZIP/Postal code"
    return null
  }

  const submitRenewForm = async () => {
    setRenewMessage(null)
    const err = validateRenewForm()
    if (err) {
      setErrorModalMessage(err)
      return
    }

    setRenewLoading(true)
    try {
      const policyData = {
        provider: renewProvider,
        member_id: renewMemberId,
        policy_number: `POL-${renewProvider.toUpperCase().replace(' ', '')}-${renewMemberId}-${Date.now()}`,
        first_name: firstName,
        last_name: renewLastName,
        dob: renewDob,
        email: email,
        phone: phone,
        address: address,
        city: city,
        state_province: stateProv,
        zip_code: zip,
        policy_type: policyType,
        coverage_status: 'ACTIVE',
        coverage_amount: 50000, // Default value, can be made configurable
        premium_amount: 100, // Default value, can be made configurable
        expiry_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split('T')[0]
      }

      const response = await fetch(`${API_BASE}/api/policies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || 'test-token'}`
        },
        body: JSON.stringify(policyData)
      })

      const result = await response.json()

      if (response.ok) {
        setRenewMessage({ type: 'success', text: 'Policy saved successfully!' })
        setToastMessage({message: 'Policy saved successfully!', type: 'success'})
        // Reset form after successful save
        setTimeout(() => {
          setFirstName('')
          setRenewLastName('')
          setRenewDob('')
          setEmail('')
          setPhone('')
          setAddress('')
          setCity('')
          setStateProv('')
          setZip('')
          setPolicyType('health')
          setRenewProvider('')
          setRenewMemberId('')
          setShowRenewForm(false)
          setRenewMessage(null)
        }, 2000)
      } else {
        const errorMessage = result.detail || result.message || 'Failed to save policy'
        setRenewMessage({ type: 'error', text: errorMessage })
        setToastMessage({message: errorMessage, type: 'error'})
      }
    } catch (error) {
      console.error('Error saving policy:', error)
      setRenewMessage({ type: 'error', text: 'Network error. Please check your connection and try again.' })
      setToastMessage({message: 'Network error. Please check your connection and try again.', type: 'error'})
    } finally {
      setRenewLoading(false)
    }
  }

  const renderResult = (data: any, title: string) => {
    if (!data) return null

    if (data.error) {
      return (
        <div className="result-card error">
          <h3>❌ {title} Error</h3>
          <p>{data.message}</p>
          {data.details && <p className="error-details">Details: {data.details}</p>}
        </div>
      )
    }

    // Handle verification results
    if (data.provider_response) {
      try {
        const policy = data.provider_response
        const status = policy.coverage_status || 'unknown'
        
        let statusIcon = '✅'
        let statusClass = 'success'
        
        if (status === 'expired') {
          statusIcon = '❌'
          statusClass = 'error'
        } else if (status === 'suspended') {
          statusIcon = '🚫'
          statusClass = 'warning'
        } else if (status === 'grace_period') {
          statusIcon = '⚠️'
          statusClass = 'warning'
        } else if (status === 'pending_verification') {
          statusIcon = '⏳'
          statusClass = 'info'
        }

        return (
          <div className={`result-card ${statusClass}`}>
            <h3>{statusIcon} Verification Result</h3>
            <div className="policy-details">
              <div className="detail-row">
                <strong>Policy Number:</strong> {policy.policy_number || 'N/A'}
              </div>
              {policy.member_name && (
                <div className="detail-row">
                  <strong>Member Name:</strong> {policy.member_name}
                </div>
              )}
              <div className="detail-row">
                <strong>Provider:</strong> {policy.provider || 'Unknown'}
              </div>
              <div className="detail-row">
                <strong>Status:</strong> <span className={`status-badge ${statusClass}`}>{status.replace('_', ' ').toUpperCase()}</span>
              </div>
              {policy.coverage_amount && (
                <div className="detail-row">
                  <strong>Coverage Amount:</strong> {policy.coverage_amount}
                </div>
              )}
              {policy.expiry_date && (
                <div className="detail-row">
                  <strong>Expiry Date:</strong> {policy.expiry_date}
                </div>
              )}
              {policy.premium_status && (
                <div className="detail-row">
                  <strong>Premium Status:</strong> {policy.premium_status.replace('_', ' ').toUpperCase()}
                </div>
              )}
              {policy.last_payment_date && (
                <div className="detail-row">
                  <strong>Last Payment:</strong> {policy.last_payment_date}
                </div>
              )}
            </div>
            {policy.message && (
              <div className="policy-message">
                <p>{policy.message}</p>
              </div>
            )}
          </div>
        )
      } catch (renderError) {
        console.error('renderResult: Error rendering verification result:', renderError)
        return (
          <div className="result-card error">
            <h3>❌ Rendering Error</h3>
            <p>Unable to display verification result due to data format issue.</p>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )
      }
    }

    // Handle policy info results
    if (data.policy_number) {
      try {
        const status = data.coverage_status || 'unknown'
        let statusIcon = '✅'
        let statusClass = 'success'
        
        if (status === 'expired') {
          statusIcon = '❌'
          statusClass = 'error'
        } else if (status === 'suspended') {
          statusIcon = '🚫'
          statusClass = 'warning'
        } else if (status === 'grace_period') {
          statusIcon = '⚠️'
          statusClass = 'warning'
        } else if (status === 'pending_verification') {
          statusIcon = '⏳'
          statusClass = 'info'
        }

        return (
          <div className={`result-card ${statusClass}`}>
            <h3>{statusIcon} Policy Information</h3>
            <div className="policy-details">
              <div className="detail-row">
                <strong>Policy Number:</strong> {data.policy_number || 'N/A'}
              </div>
              <div className="detail-row">
                <strong>Status:</strong> <span className={`status-badge ${statusClass}`}>{status.replace('_', ' ').toUpperCase()}</span>
              </div>
              {data.coverage_amount && (
                <div className="detail-row">
                  <strong>Coverage Amount:</strong> {data.coverage_amount}
                </div>
              )}
              {data.expiry_date && (
                <div className="detail-row">
                  <strong>Expiry Date:</strong> {data.expiry_date}
                </div>
              )}
              {data.premium_status && (
                <div className="detail-row">
                  <strong>Premium Status:</strong> {data.premium_status.replace('_', ' ').toUpperCase()}
                </div>
              )}
              {data.next_payment_due && (
                <div className="detail-row">
                  <strong>Next Payment Due:</strong> {data.next_payment_due}
                </div>
              )}
            </div>
          </div>
        )
      } catch (renderError) {
        console.error('renderResult: Error rendering policy info result:', renderError)
        return (
          <div className="result-card error">
            <h3>❌ Rendering Error</h3>
            <p>Unable to display policy information due to data format issue.</p>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )
      }
    }

    // Handle not found results
    if (data.status === 'not_found') {
      return (
        <div className="result-card error">
          <h3>❓ Policy Not Found</h3>
          <p>{data.message}</p>
        </div>
      )
    }

    // Fallback to JSON display for unexpected formats
    return (
      <div className="result-card">
        <h3>{title}</h3>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    )
  }

  return (
    <div>
      <div className="grid grid-2">
        <label>Provider
          <select value={provider} onChange={e => setProvider(e.target.value)}>
            <option value="statelife">State Life</option>
            <option value="efu">EFU</option>
            <option value="jubilee">Jubilee</option>
          </select>
        </label>
        <label>Member ID
          <input
            value={memberId}
            onChange={e => {
              const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 6)
              setMemberId(digitsOnly)
            }}
            placeholder="123456"
            maxLength={6}
            inputMode="numeric"
            pattern="[0-9]*"
          />
        </label>
        <label>Date of Birth
          <input type="date" value={dob} min="1950-01-01" onChange={e => setDob(e.target.value)} />
        </label>
        <label>Last Name
          <input value={lastName} onChange={e => setLastName(e.target.value)} placeholder="Doe" />
        </label>
      </div>
      <div className="actions">
        <button className="btn" onClick={callVerify} disabled={loading}>Submit Verification</button>
        <button className="btn secondary" onClick={callPolicyInfo} disabled={loading}>Get Policy Info</button>
        <button className="btn secondary" onClick={clearAll} disabled={loading}>Clear All</button>
        <button className="btn" onClick={() => { setShowRenewForm(true); setRenewMessage(null) }} disabled={loading}>
          Renew/Add New Policy
        </button>
        <button className="btn secondary" onClick={handleViewSavedPolicies} disabled={loading}>
          View Saved Policies
        </button>
      </div>
      <Modal
        isOpen={showRenewForm}
        onClose={() => { setShowRenewForm(false); setRenewMessage(null) }}
        title="Renew/Add New Policy"
        size="md"
        footer={
          <div className="actions">
            <button className="btn" onClick={submitRenewForm} disabled={renewLoading}>
              {renewLoading ? 'Saving...' : 'Save Policy'}
            </button>
            <button className="btn secondary" onClick={() => { setShowRenewForm(false); setRenewMessage(null) }} disabled={renewLoading}>
              Cancel
            </button>
          </div>
        }
      >
        <div className="grid grid-2">
          <label>Provider <span className="required">*</span>
            <select value={renewProvider} onChange={e => setRenewProvider(e.target.value)}>
              <option value="">Select Provider</option>
              <option value="State Life">State Life</option>
              <option value="EFU">EFU</option>
              <option value="Jubilee">Jubilee</option>
            </select>
          </label>
          <label>Member ID <span className="required">*</span>
            <input
              value={renewMemberId}
              onChange={handleRenewMemberIdChange}
              placeholder="123456"
              maxLength={6}
              inputMode="numeric"
              pattern="[0-9]*"
            />
          </label>
          <label>First Name
            <input value={firstName} onChange={e => setFirstName(e.target.value)} placeholder="John" />
          </label>
          <label>Last Name
            <input value={renewLastName} onChange={e => setRenewLastName(e.target.value)} placeholder="Doe" />
          </label>
          <label>Date of Birth
            <input type="date" value={renewDob} min="1950-01-01" onChange={e => setRenewDob(e.target.value)} />
          </label>
          <label>Email
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="john.doe@email.com" />
          </label>
          <label>Phone
            <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+1 555 123 4567" />
          </label>
          <label>Address
            <input value={address} onChange={e => setAddress(e.target.value)} placeholder="123 Main St" />
          </label>
          <label>City
            <input value={city} onChange={e => setCity(e.target.value)} placeholder="New York" />
          </label>
          <label>State/Province
            <input value={stateProv} onChange={e => setStateProv(e.target.value)} placeholder="NY" />
          </label>
          <label>ZIP/Postal Code
            <input value={zip} onChange={e => setZip(e.target.value)} placeholder="10001" />
          </label>
          <label>Policy Type
            <select value={policyType} onChange={e => setPolicyType(e.target.value)}>
              <option value="health">Health</option>
              <option value="life">Life</option>
              <option value="auto">Auto</option>
              <option value="home">Home</option>
            </select>
          </label>
        </div>
        {renewMessage && (
          <div className={`result-card ${renewMessage.type === 'success' ? 'success' : 'error'}`} style={{ marginTop: 12 }}>
            <h3>{renewMessage.type === 'success' ? '✅ Success' : '❌ Error'}</h3>
            <p>{renewMessage.text}</p>
          </div>
        )}
      </Modal>
      
      {/* Error Modal */}
      <Modal
        isOpen={errorModalMessage !== null}
        onClose={() => setErrorModalMessage(null)}
        title="Validation Error"
        size="xs"
        footer={
          <div className="actions">
            <button className="btn compact" onClick={() => setErrorModalMessage(null)}>
              OK
            </button>
          </div>
        }
      >
        <div className="error-modal-content compact">
          <p>{errorModalMessage}</p>
        </div>
      </Modal>

      {/* Toast Notifications */}
      {toastMessage && (
        <Toast
          message={toastMessage.message}
          type={toastMessage.type}
          duration={3000}
          onClose={() => setToastMessage(null)}
        />
      )}
      
      {renderResult(result, 'Verification')}
      {renderResult(policy, 'Policy Information')}

      {/* View Saved Policies Modal */}
      <Modal
        isOpen={showSavedPolicies}
        onClose={() => setShowSavedPolicies(false)}
        title="Saved Policies"
        size="lg"
        footer={
          <div className="actions">
            <button className="btn" onClick={() => setShowSavedPolicies(false)}>
              Close
            </button>
          </div>
        }
      >
        {savedPoliciesLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading saved policies...</p>
          </div>
        ) : savedPolicies.length === 0 ? (
          <div className="empty-state">
            <p>No saved policies found.</p>
            <p>Click "Renew/Add New Policy" to create your first policy.</p>
          </div>
        ) : (
          <div className="policies-table-container">
            <table className="policies-table">
              <thead>
                <tr>
                  <th>Policy Number</th>
                  <th>Provider</th>
                  <th>Member ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Expiry Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {savedPolicies.map((policy) => (
                  <tr key={policy.id}>
                    <td>{policy.policy_number}</td>
                    <td>{policy.provider}</td>
                    <td>{policy.member_id}</td>
                    <td>{`${policy.first_name || ''} ${policy.last_name || ''}`.trim()}</td>
                    <td>{policy.policy_type?.toUpperCase() || 'N/A'}</td>
                    <td>
                      <span className={`status-badge ${policy.coverage_status?.toLowerCase() || 'unknown'}`}>
                        {policy.coverage_status?.replace('_', ' ').toUpperCase() || 'N/A'}
                      </span>
                    </td>
                    <td>{policy.expiry_date || 'N/A'}</td>
                    <td>
                      <div className="action-buttons">
                        <button 
                          className="btn compact secondary" 
                          onClick={() => handleEditPolicy(policy)}
                          title="Edit Policy"
                        >
                          ✏️
                        </button>
                        <button 
                          className="btn compact danger" 
                          onClick={() => handleDeletePolicy(policy.id)}
                          title="Delete Policy"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteConfirmModal}
        onClose={() => {
          setShowDeleteConfirmModal(false)
          setPolicyToDelete(null)
        }}
        title="Confirm Deletion"
        size="sm"
        footer={
          <div className="actions">
            <button 
              className="btn secondary" 
              onClick={() => {
                setShowDeleteConfirmModal(false)
                setPolicyToDelete(null)
              }}
            >
              Cancel
            </button>
            <button 
              className="btn danger" 
              onClick={confirmDeletePolicy}
            >
              Delete
            </button>
          </div>
        }
      >
        <div className="delete-confirm-content">
          <p>Are you sure you want to delete this policy?</p>
          <p className="delete-warning">This action cannot be undone.</p>
        </div>
      </Modal>

      {/* Edit Policy Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingPolicy(null)
        }}
        title="Edit Policy Details"
        size="md"
        footer={
          <div className="actions">
            <button 
              className="btn secondary" 
              onClick={() => {
                setShowEditModal(false)
                setEditingPolicy(null)
              }}
              disabled={renewLoading}
            >
              Cancel
            </button>
            <button 
              className="btn" 
              onClick={handleUpdatePolicy}
              disabled={renewLoading}
            >
              {renewLoading ? 'Saving...' : 'Save'}
            </button>
          </div>
        }
      >
        {editingPolicy && (
          <div className="grid grid-2">
            <label>Provider <span className="required">*</span>
              <select 
                value={editingPolicy.provider || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, provider: e.target.value})}
              >
                <option value="">Select Provider</option>
                <option value="State Life">State Life</option>
                <option value="EFU">EFU</option>
                <option value="Jubilee">Jubilee</option>
              </select>
            </label>
            <label>Member ID <span className="required">*</span>
              <input
                value={editingPolicy.member_id || ''}
                onChange={e => setEditingPolicy({...editingPolicy, member_id: e.target.value})}
                placeholder="123456"
                maxLength={6}
                inputMode="numeric"
                pattern="[0-9]*"
              />
            </label>
            <label>First Name
              <input 
                value={editingPolicy.first_name || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, first_name: e.target.value})} 
                placeholder="John" 
              />
            </label>
            <label>Last Name
              <input 
                value={editingPolicy.last_name || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, last_name: e.target.value})} 
                placeholder="Doe" 
              />
            </label>
            <label>Date of Birth
              <input 
                type="date" 
                value={editingPolicy.dob || ''} 
                min="1950-01-01" 
                onChange={e => setEditingPolicy({...editingPolicy, dob: e.target.value})} 
              />
            </label>
            <label>Email
              <input 
                value={editingPolicy.email || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, email: e.target.value})} 
                placeholder="john.doe@email.com" 
              />
            </label>
            <label>Phone
              <input 
                value={editingPolicy.phone || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, phone: e.target.value})} 
                placeholder="+1 555 123 4567" 
              />
            </label>
            <label>Address
              <input 
                value={editingPolicy.address || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, address: e.target.value})} 
                placeholder="123 Main St" 
              />
            </label>
            <label>City
              <input 
                value={editingPolicy.city || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, city: e.target.value})} 
                placeholder="New York" 
              />
            </label>
            <label>State/Province
              <input 
                value={editingPolicy.state_province || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, state_province: e.target.value})} 
                placeholder="NY" 
              />
            </label>
            <label>ZIP/Postal Code
              <input 
                value={editingPolicy.zip_code || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, zip_code: e.target.value})} 
                placeholder="10001" 
              />
            </label>
            <label>Policy Type
              <select 
                value={editingPolicy.policy_type || 'health'} 
                onChange={e => setEditingPolicy({...editingPolicy, policy_type: e.target.value})}
              >
                <option value="health">Health</option>
                <option value="life">Life</option>
                <option value="auto">Auto</option>
                <option value="home">Home</option>
              </select>
            </label>
            <label>Coverage Status
              <select 
                value={editingPolicy.coverage_status || 'ACTIVE'} 
                onChange={e => setEditingPolicy({...editingPolicy, coverage_status: e.target.value})}
              >
                <option value="ACTIVE">Active</option>
                <option value="EXPIRED">Expired</option>
                <option value="SUSPENDED">Suspended</option>
                <option value="PENDING">Pending</option>
                <option value="GRACE_PERIOD">Grace Period</option>
              </select>
            </label>
            <label>Expiry Date
              <input 
                type="date" 
                value={editingPolicy.expiry_date || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, expiry_date: e.target.value})} 
              />
            </label>
            <label>Coverage Amount
              <input 
                type="number" 
                value={editingPolicy.coverage_amount || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, coverage_amount: parseFloat(e.target.value) || 0})} 
                placeholder="50000" 
              />
            </label>
            <label>Premium Amount
              <input 
                type="number" 
                value={editingPolicy.premium_amount || ''} 
                onChange={e => setEditingPolicy({...editingPolicy, premium_amount: parseFloat(e.target.value) || 0})} 
                placeholder="100" 
              />
            </label>
          </div>
        )}
      </Modal>

      <SavedPoliciesStyles />
    </div>
  )
}

/* Styles for Saved Policies Modal */
const SavedPoliciesStyles = () => (
  <style>{`
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      text-align: center;
    }
    
    .loading-spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #f3f3f3;
      border-top: 4px solid #007bff;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 1rem;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    .empty-state {
      text-align: center;
      padding: 2rem;
      color: #6c757d;
    }
    
    .empty-state p:first-child {
      font-size: 1.1rem;
      font-weight: 500;
      margin-bottom: 0.5rem;
      color: #495057;
    }
    
    .empty-state p:last-child {
      font-size: 0.9rem;
      margin: 0;
    }
    
    .policies-table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #dee2e6;
      border-radius: 0.375rem;
      margin: 1rem 0;
    }
    
    .policies-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }
    
    .policies-table th {
      background-color: #f8f9fa;
      border-bottom: 2px solid #dee2e6;
      padding: 0.75rem;
      text-align: left;
      font-weight: 600;
      color: #495057;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    .policies-table td {
      padding: 0.75rem;
      border-bottom: 1px solid #dee2e6;
      vertical-align: middle;
    }
    
    .policies-table tr {
      transition: background-color 0.2s ease-in-out;
    }
    
    .policies-table tr:hover {
      background-color: rgba(79, 140, 255, 0.08);
    }

    @media (prefers-color-scheme: dark) {
      .policies-table tr:hover {
        background-color: rgba(79, 140, 255, 0.15);
      }
    }
    
    .policies-table tr:last-child td {
      border-bottom: none;
    }
    
    .status-badge {
      display: inline-block;
      padding: 0.25rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.025em;
    }
    
    .status-badge.pending {
      background-color: #fff3cd;
      color: #856404;
      border: 1px solid #ffeaa7;
    }
    
    .status-badge.active {
      background-color: #d4edda;
      color: #155724;
      border: 1px solid #c3e6cb;
    }
    
    .status-badge.expired {
      background-color: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
    }
    
    .status-badge.suspended {
      background-color: #e2e3e5;
      color: #383d41;
      border: 1px solid #d6d8db;
    }
    
    .status-badge.grace_period {
      background-color: #cce5ff;
      color: #004085;
      border: 1px solid #b8daff;
    }
    
    .status-badge.unknown {
      background-color: #f8f9fa;
      color: #6c757d;
      border: 1px solid #dee2e6;
    }
    
    .action-buttons {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }
    
    .btn.compact {
      padding: 0.375rem 0.75rem;
      font-size: 0.875rem;
      min-height: 32px;
    }
    
    .btn.compact.secondary {
      background-color: #6c757d;
      border-color: #6c757d;
    }
    
    .btn.compact.secondary:hover {
      background-color: #5a6268;
      border-color: #545b62;
    }
    
    .btn.compact.danger {
      background-color: #dc3545;
      border-color: #dc3545;
    }
    
    .btn.compact.danger:hover {
      background-color: #c82333;
      border-color: #bd2130;
    }
    
    .error-modal-content.compact p {
      margin: 0;
      padding: 0.5rem 0;
    }
    
    .success-modal-content {
      text-align: center;
      color: #155724;
    }
    
    .success-modal-content p {
      margin: 0;
      padding: 0.5rem 0;
      font-weight: 500;
    }
    
    .success-modal-content p {
      margin: 0;
      padding: 0.5rem 0;
    }
    
    /* Delete Confirmation Modal Styles */
    .delete-confirm-content {
      text-align: center;
      padding: 1rem 0;
    }
    
    .delete-confirm-content p {
      margin: 0.5rem 0;
      color: var(--text);
      font-size: 1rem;
      line-height: 1.5;
    }
    
    .delete-warning {
      color: var(--danger) !important;
      font-size: 0.875rem !important;
      font-weight: 500;
      opacity: 0.8;
    }
    
    .btn.danger {
      background: var(--danger) !important;
      border-color: var(--danger) !important;
    }
    
    .btn.danger:hover {
      background: #ff5252 !important;
      border-color: #ff5252 !important;
      transform: translateY(-1px);
    }
    
    .btn.danger:active {
      transform: translateY(0);
    }
  `}</style>
)


