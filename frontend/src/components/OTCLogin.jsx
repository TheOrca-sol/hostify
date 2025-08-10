import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from './Toaster'
import { Phone, MessageSquare, ArrowLeft } from 'lucide-react'
import { useAuth } from '../services/auth'

export default function OTCLogin() {
  const [step, setStep] = useState('phone') // 'phone' or 'code'
  const [phoneNumber, setPhoneNumber] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const navigate = useNavigate()
  const { signInWithOTC } = useAuth()

  const handleSendCode = async (e) => {
    e.preventDefault()
    
    if (!phoneNumber.trim()) {
      toast.error('Please enter your phone number')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/sms-auth/login/send-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber })
      })

      const result = await response.json()
      
      if (result.success) {
        toast.success('Verification code sent to your phone!')
        setStep('code')
        setCountdown(60)
        startCountdown()
      } else {
        toast.error(result.error || 'Failed to send verification code')
      }
    } catch (error) {
      console.error('Error sending code:', error)
      toast.error('Failed to send verification code')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyCode = async (e) => {
    e.preventDefault()
    
    if (!verificationCode.trim()) {
      toast.error('Please enter the verification code')
      return
    }

    setLoading(true)
    try {
      await signInWithOTC(phoneNumber, verificationCode)
      toast.success('Successfully logged in!')
      navigate('/dashboard')
    } catch (error) {
      console.error('Error verifying code:', error)
      toast.error(error.message || 'Invalid verification code')
    } finally {
      setLoading(false)
    }
  }

  const startCountdown = () => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const handleResendCode = () => {
    if (countdown > 0) return
    handleSendCode({ preventDefault: () => {} })
  }

  const handleBack = () => {
    setStep('phone')
    setVerificationCode('')
    setCountdown(0)
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="text-center mb-6">
        <div className="mx-auto h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <MessageSquare className="h-6 w-6 text-blue-600" />
        </div>
        <h3 className="text-lg font-medium text-gray-900">
          {step === 'phone' ? 'Enter Phone Number' : 'Enter Verification Code'}
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {step === 'phone' 
            ? 'We\'ll send a verification code to your phone'
            : `Code sent to ${phoneNumber}`
          }
        </p>
      </div>

      {step === 'phone' ? (
        <form onSubmit={handleSendCode} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="+1234567890"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Sending...' : 'Send Verification Code'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyCode} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Verification Code
            </label>
            <input
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-lg tracking-widest"
              placeholder="123456"
              maxLength="6"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Verifying...' : 'Verify Code'}
          </button>

          <div className="text-center space-y-2">
            <button
              type="button"
              onClick={handleBack}
              className="flex items-center justify-center w-full text-sm text-gray-600 hover:text-gray-800"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Phone Number
            </button>

            <div className="text-sm text-gray-500">
              Didn't receive the code?{' '}
              <button
                type="button"
                onClick={handleResendCode}
                disabled={countdown > 0}
                className="text-blue-600 hover:text-blue-500 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                {countdown > 0 ? `Resend in ${countdown}s` : 'Resend Code'}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}
