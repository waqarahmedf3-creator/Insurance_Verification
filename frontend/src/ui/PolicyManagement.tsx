import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const AUTH = 'Bearer dev-secret';

export const PolicyManagement: React.FC = () => {
  const navigate = useNavigate();
  const [view, setView] = useState<'initial' | 'add' | 'renew'>('initial');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Form fields
  const [memberId, setMemberId] = useState('');
  const [avatar, setAvatar] = useState<string | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [provider, setProvider] = useState('');
  const [policyType, setPolicyType] = useState('');
  const [coverageAmount, setCoverageAmount] = useState('');
  const [premiumAmount, setPremiumAmount] = useState('');

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          setAvatar(e.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleMemberIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, ''); // Remove non-numeric characters
    if (value.length <= 6) {
      setMemberId(value);
    }
  };

  const handleLoadPolicy = async () => {
    if (!memberId || memberId.trim() === '') {
      setMessage({ type: 'error', text: 'Member ID is required' });
      return;
    }
    if (!/^\d{6}$/.test(memberId)) {
      setMessage({ type: 'error', text: 'Member ID must be exactly 6 digits' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const resp = await fetch(`${API_BASE}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': AUTH },
        body: JSON.stringify({ memberId })
      });
      
      const data = await resp.json();
      
      if (data.error) {
        setMessage({ type: 'error', text: 'Policy not found. Please check the Member ID.' });
      } else {
        // Pre-fill form with data from API
        setFirstName(data.first_name || '');
        setLastName(data.last_name || '');
        setDob(data.dob || '');
        setEmail(data.email || '');
        setPhone(data.phone || '');
        setAddress(data.address || '');
        setProvider(data.provider || '');
        setPolicyType(data.policy_type || '');
        setCoverageAmount(data.coverage_amount || '');
        setPremiumAmount(data.premium_amount || '');
        
        setMessage({ type: 'success', text: 'Policy data loaded successfully!' });
        setView('add'); // Switch to form view
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load policy data. Please try again.' });
    }
    
    setLoading(false);
  };

  const validateForm = () => {
    const errors = [];
    
    if (!firstName.trim()) errors.push('First Name is required');
    if (!lastName.trim()) errors.push('Last Name is required');
    if (!dob) errors.push('Date of Birth is required');
    if (dob && new Date(dob) < new Date('1950-01-01')) 
      errors.push('Date of Birth cannot be earlier than 01/01/1950');
    if (!policyType.trim()) errors.push('Policy Type is required');
    if (!premiumAmount.trim()) errors.push('Premium Amount is required');
    
    // Member ID validation
    if (!memberId || memberId.trim() === '') { 
      errors.push('Member ID is required'); 
    } else if (!/^\d{6}$/.test(memberId)) { 
      errors.push('Member ID must be exactly 6 digits'); 
    }
    
    // Provider validation
    if (!provider || provider === '') { 
      errors.push('Provider is required'); 
    }
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSavePolicy = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    setMessage(null);
    
    try {
      const policyData = {
        avatar,
        first_name: firstName,
        last_name: lastName,
        dob,
        email,
        phone,
        address,
        provider,
        member_id: memberId,
        policy_type: policyType,
        coverage_amount: coverageAmount,
        premium_amount: premiumAmount
      };
      
      const resp = await fetch(`${API_BASE}/api/policy-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': AUTH },
        body: JSON.stringify(policyData)
      });
      
      if (resp.ok) {
        setMessage({ type: 'success', text: 'Policy saved successfully!' });
        // Clear form fields
        setAvatar(null);
        setFirstName('');
        setLastName('');
        setDob('');
        setEmail('');
        setPhone('');
        setAddress('');
        setProvider('');
        setMemberId('');
        setPolicyType('');
        setCoverageAmount('');
        setPremiumAmount('');
      } else {
        setMessage({ type: 'error', text: 'Failed to save policy. Please try again.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save policy. Please try again.' });
    }
    
    setLoading(false);
  };

  const renderInitialView = () => (
    <div className="p-6">
      <div className="section-header">
        <h2 className="section-title">Policy Management Dashboard</h2>
        <p className="section-subtitle">Manage and renew insurance policies</p>
      </div>
      <div className="flex flex-col md:flex-row gap-4 w-full max-w-md mx-auto">
        <button
          onClick={() => setView('add')}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors w-full"
        >
          Add New Policy
        </button>
        
        <button
          onClick={() => setView('renew')}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-6 rounded-lg transition-colors w-full"
        >
          Renew Policy
        </button>
      </div>
    </div>
  );

  const renderRenewView = () => (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="section-header">
        <h2 className="section-title">Renew Insurance Policy</h2>
        <p className="section-subtitle">Update and extend existing policy coverage</p>
      </div>
      
      {message && (
        <div className={`p-4 mb-6 rounded-lg flex items-center ${
          message.type === 'success' ? 'bg-green-800/50' : 'bg-red-800/50'
        }`}>
          {message.type === 'success' ? 
            <CheckCircle className="h-5 w-5 text-green-400 mr-2" /> : 
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
          }
          <span className="text-white">{message.text}</span>
        </div>
      )}
      
      <div className="bg-slate-800 p-6 rounded-lg shadow-lg">
        <div className="mb-6">
          <label className="block text-white mb-2">
            Member ID <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={memberId}
              onChange={handleMemberIdChange}
              className="bg-slate-700 text-white rounded-lg p-3 flex-1 focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter 6-digit Member ID"
              maxLength={6}
            />
            <button
              onClick={handleLoadPolicy}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load Policy Data'}
            </button>
          </div>
        </div>
        
        
        {/* Policy Form - Only show after data is loaded */}
        {(firstName || lastName || email || phone) && (
          <>
            {validationErrors.length > 0 && (
              <div className="bg-red-800/50 p-4 mb-6 rounded-lg">
                <div className="flex items-center mb-2">
                  <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
                  <span className="text-white font-medium">Please fix the following errors:</span>
                </div>
                <ul className="list-disc pl-10 text-red-300">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Avatar Upload */}
              <div className="flex flex-col items-center justify-center col-span-2 md:col-span-1">
                <div 
                  className="w-32 h-32 rounded-full bg-slate-700 flex items-center justify-center overflow-hidden cursor-pointer mb-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {avatar ? (
                    <img src={avatar} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <Camera className="h-10 w-10 text-slate-400" />
                  )}
                </div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleAvatarChange}
                  className="hidden"
                  accept="image/*"
                />
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-400 text-sm"
                >
                  Upload Profile Image
                </button>
              </div>
              
              {/* First Name */}
              <div>
                <label className="block text-white mb-2">
                  First Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter first name"
                />
              </div>
              
              {/* Last Name */}
              <div>
                <label className="block text-white mb-2">
                  Last Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter last name"
                />
              </div>
              
              {/* Date of Birth */}
              <div>
                <label className="block text-white mb-2">
                  Date of Birth <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  min="1950-01-01"
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              
              {/* Email */}
              <div>
                <label className="block text-white mb-2">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter email address"
                />
              </div>
              
              {/* Phone */}
              <div>
                <label className="block text-white mb-2">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter phone number"
                />
              </div>
              
              {/* Address */}
              <div className="col-span-2">
                <label className="block text-white mb-2">Address</label>
                <textarea
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter address"
                  rows={3}
                />
              </div>
              
              {/* Provider - New Mandatory Field */}
              <div>
                <label className="block text-white mb-2">
                  Provider <span className="text-red-500">*</span>
                </label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none h-12"
                >
                  <option value="">Select Provider</option>
                  <option value="State Life">State Life</option>
                  <option value="EFU">EFU</option>
                  <option value="Jubilee">Jubilee</option>
                </select>
              </div>
              
              {/* Member ID - New Mandatory Field */}
              <div>
                <label className="block text-white mb-2">
                  Member ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={memberId}
                  onChange={handleMemberIdChange}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter 6-digit Member ID"
                  maxLength={6}
                />
              </div>
              
              {/* Policy Type */}
              <div>
                <label className="block text-white mb-2">
                  Policy Type <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={policyType}
                  onChange={(e) => setPolicyType(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter policy type"
                />
              </div>
              
              {/* Coverage Amount */}
              <div>
                <label className="block text-white mb-2">Coverage Amount</label>
                <input
                  type="text"
                  value={coverageAmount}
                  onChange={(e) => setCoverageAmount(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter coverage amount"
                />
              </div>
              
              {/* Premium Amount */}
              <div>
                <label className="block text-white mb-2">
                  Premium Amount <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={premiumAmount}
                  onChange={(e) => setPremiumAmount(e.target.value)}
                  className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Enter premium amount"
                />
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <div>
                <button
                  onClick={() => setView('initial')}
                  className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg transition-colors mr-2"
                >
                  Back
                </button>
                <button
                  onClick={() => {
                    setView('initial');
                    setValidationErrors([]);
                    setMessage(null);
                  }}
                  className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
              
              <button
                onClick={handleSavePolicy}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Renewing...' : 'Renew Policy'}
              </button>
            </div>
          </>
        )}
        
        <div className="flex justify-between mt-6">
          <button
            onClick={() => setView('initial')}
            className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Back
          </button>
        </div>
      </div>
    </div>
  );

  const renderPolicyForm = () => (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="section-header">
        <h2 className="section-title">{view === 'add' ? 'Add New Policy' : 'Renew Insurance Policy'}</h2>
        <p className="section-subtitle">{view === 'add' ? 'Create a new insurance policy' : 'Update and extend existing policy coverage'}</p>
      </div>
      
      {message && (
        <div className={`p-4 mb-6 rounded-lg flex items-center ${
          message.type === 'success' ? 'bg-green-800/50' : 'bg-red-800/50'
        }`}>
          {message.type === 'success' ? 
            <CheckCircle className="h-5 w-5 text-green-400 mr-2" /> : 
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
          }
          <span className="text-white">{message.text}</span>
        </div>
      )}
      
      {validationErrors.length > 0 && (
        <div className="bg-red-800/50 p-4 mb-6 rounded-lg">
          <div className="flex items-center mb-2">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-white font-medium">Please fix the following errors:</span>
          </div>
          <ul className="list-disc pl-10 text-red-300">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="bg-slate-800 p-6 rounded-lg shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Avatar Upload */}
          <div className="flex flex-col items-center justify-center col-span-2 md:col-span-1">
            <div 
              className="w-32 h-32 rounded-full bg-slate-700 flex items-center justify-center overflow-hidden cursor-pointer mb-2"
              onClick={() => fileInputRef.current?.click()}
            >
              {avatar ? (
                <img src={avatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <Camera className="h-10 w-10 text-slate-400" />
              )}
            </div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleAvatarChange}
              className="hidden"
              accept="image/*"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="text-blue-400 text-sm"
            >
              Upload Profile Image
            </button>
          </div>
          
          {/* First Name */}
          <div>
            <label className="block text-white mb-2">
              First Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter first name"
            />
          </div>
          
          {/* Last Name */}
          <div>
            <label className="block text-white mb-2">
              Last Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter last name"
            />
          </div>
          
          {/* Date of Birth */}
          <div>
            <label className="block text-white mb-2">
              Date of Birth <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              min="1950-01-01"
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          
          {/* Email */}
          <div>
            <label className="block text-white mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter email address"
            />
          </div>
          
          {/* Phone */}
          <div>
            <label className="block text-white mb-2">Phone</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter phone number"
            />
          </div>
          
          {/* Address */}
          <div className="col-span-2">
            <label className="block text-white mb-2">Address</label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter address"
              rows={3}
            />
          </div>
          
          {/* Provider */}
          <div>
            <label className="block text-white mb-2">
              Provider <span className="text-red-500">*</span>
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none h-12"
            >
              <option value="">Select Provider</option>
              <option value="State Life">State Life</option>
              <option value="EFU">EFU</option>
              <option value="Jubilee">Jubilee</option>
            </select>
          </div>
          
          {/* Member ID */}
          <div>
            <label className="block text-white mb-2">
              Member ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={memberId}
              onChange={handleMemberIdChange}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter 6-digit Member ID"
              maxLength={6}
            />
          </div>
          
          {/* Policy Type */}
          <div>
            <label className="block text-white mb-2">
              Policy Type <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={policyType}
              onChange={(e) => setPolicyType(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter policy type"
            />
          </div>
          
          {/* Coverage Amount */}
          <div>
            <label className="block text-white mb-2">Coverage Amount</label>
            <input
              type="text"
              value={coverageAmount}
              onChange={(e) => setCoverageAmount(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter coverage amount"
            />
          </div>
          
          {/* Premium Amount */}
          <div>
            <label className="block text-white mb-2">
              Premium Amount <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={premiumAmount}
              onChange={(e) => setPremiumAmount(e.target.value)}
              className="bg-slate-700 text-white rounded-lg p-3 w-full focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Enter premium amount"
            />
          </div>
        </div>
        
        <div className="flex justify-between mt-8">
          <div>
            <button
              onClick={() => navigate('/')}
              className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg transition-colors mr-2"
            >
              Back
            </button>
            <button
              onClick={() => {
                setView('initial');
                setValidationErrors([]);
                setMessage(null);
              }}
              className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
          
          <button
            onClick={handleSavePolicy}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Policy'}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900">
      {view === 'initial' && renderInitialView()}
      {view === 'renew' && renderRenewView()}
      {view === 'add' && renderPolicyForm()}
    </div>
  );
};