import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { api } from '../services/api'
import { Users, Crown, Sparkles, Wrench, Eye, Mail, Lock, CheckCircle, AlertCircle } from 'lucide-react'
import { toast } from '../components/Toaster'

const ROLE_CONFIG = {
  cohost: {
    icon: Users,
    label: 'Co-Host',
    description: 'Full property management access',
    color: 'blue'
  },
  agency: {
    icon: Crown,
    label: 'Agency',
    description: 'Professional management company',
    color: 'purple'
  },
  cleaner: {
    icon: Sparkles,
    label: 'Cleaner',
    description: 'Cleaning tasks and schedules',
    color: 'green'
  },
  maintenance: {
    icon: Wrench,
    label: 'Maintenance',
    description: 'Repairs and maintenance tasks',
    color: 'orange'
  },
  assistant: {
    icon: Eye,
    label: 'Assistant',
    description: 'View-only access',
    color: 'gray'
  }
}

export default function InvitationAcceptance() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { 
    user, 
    signInWithGoogle, 
    signUpWithEmail, 
    signInWithEmail, 
    resetPassword,
    loading: authLoading 
  } = useAuth()

  const [invitation, setInvitation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [authMode, setAuthMode] = useState('choose') // 'choose', 'signin', 'signup'
  const [authInProgress, setAuthInProgress] = useState(false)
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (token) {
      loadInvitation()
    }
  }, [token])

  useEffect(() => {
    // If user is already authenticated and we have an invitation, accept it automatically
    if (user && invitation && !success) {
      handleAcceptInvitation()
    }
  }, [user, invitation])

  const loadInvitation = async () => {
    try {
      setLoading(true)
      setError('')
      
      const result = await api.getInvitationDetails(token)
      if (result.success) {
        setInvitation(result.invitation)
        setAuthForm(prev => ({ ...prev, email: result.invitation.invited_email }))
      } else {
        setError(result.error || 'Invalid or expired invitation')
      }
    } catch (err) {
      setError('Failed to load invitation details')
    } finally {
      setLoading(false)
    }
  }

  const handleAcceptInvitation = async () => {
    try {
      const result = await api.acceptInvitation(token)
      if (result.success) {
        setSuccess(true)
        toast.success('Welcome to the team! Redirecting to your dashboard...')
        setTimeout(() => {
          navigate('/dashboard')
        }, 2000)
      } else {
        setError(result.error || 'Failed to accept invitation')
      }
    } catch (err) {
      setError('Failed to accept invitation')
    }
  }

  const handleGoogleSignIn = async () => {
    try {
      setAuthInProgress(true)
      setError('')
      await signInWithGoogle()
      // Auto-acceptance happens in useEffect when user is set
    } catch (err) {
      setError(err.message || 'Google sign-in failed')
    } finally {
      setAuthInProgress(false)
    }
  }

  const handleEmailAuth = async (e) => {
    e.preventDefault()
    
    if (authMode === 'signup') {
      if (authForm.password !== authForm.confirmPassword) {
        setError('Passwords do not match')
        return
      }
      if (authForm.password.length < 6) {
        setError('Password must be at least 6 characters')
        return
      }
    }

    try {
      setAuthInProgress(true)
      setError('')

      if (authMode === 'signup') {
        await signUpWithEmail(authForm.email, authForm.password, authForm.name)
      } else {
        await signInWithEmail(authForm.email, authForm.password)
      }
      // Auto-acceptance happens in useEffect when user is set
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setAuthInProgress(false)
    }
  }

  const handleForgotPassword = async () => {
    if (!authForm.email) {
      setError('Please enter your email address')
      return
    }

    try {
      await resetPassword(authForm.email)
      toast.success('Password reset email sent!')
    } catch (err) {
      setError(err.message || 'Failed to send reset email')
    }
  }

  if (loading || authInProgress) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {loading ? 'Loading invitation...' : 'Processing authentication...'}
          </p>
        </div>
      </div>
    )
  }

  if (error && !invitation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Invitation</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Welcome to the Team!</h1>
          <p className="text-gray-600 mb-6">
            You've successfully joined the {invitation?.property_name} team as a {ROLE_CONFIG[invitation?.role]?.label}.
          </p>
          <div className="animate-pulse text-blue-600">Redirecting to your dashboard...</div>
        </div>
      </div>
    )
  }

  if (!invitation) {
    return null
  }

  const roleConfig = ROLE_CONFIG[invitation.role] || ROLE_CONFIG.assistant
  const RoleIcon = roleConfig.icon

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className={`inline-flex p-3 rounded-full bg-${roleConfig.color}-100 mb-4`}>
              <RoleIcon className={`w-8 h-8 text-${roleConfig.color}-600`} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              You're Invited!
            </h1>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                <strong>{invitation.inviter_name}</strong> has invited you to join
              </p>
              <p className="font-semibold text-gray-900">{invitation.property_name}</p>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${roleConfig.color}-100 text-${roleConfig.color}-800`}>
                <RoleIcon className="w-4 h-4 mr-1" />
                {roleConfig.label}
              </div>
              <p className="text-sm text-gray-500 mt-2">{roleConfig.description}</p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
                <div className="text-sm text-red-800">{error}</div>
              </div>
            </div>
          )}

          {/* Authentication Options */}
          {authMode === 'choose' && (
            <div className="space-y-4">
              <p className="text-center text-gray-600 mb-6">Choose how to sign in:</p>
              
              {/* Google Sign In */}
              <button
                onClick={handleGoogleSignIn}
                disabled={authInProgress}
                className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </button>

              {/* Email Option */}
              <button
                onClick={() => setAuthMode('signin')}
                className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Mail className="w-5 h-5 mr-3" />
                Continue with Email
              </button>

              <div className="mt-6 text-center">
                <p className="text-sm text-gray-500">
                  Don't have an account?{' '}
                  <button
                    onClick={() => setAuthMode('signup')}
                    className="font-medium text-blue-600 hover:text-blue-500"
                  >
                    Sign up here
                  </button>
                </p>
              </div>
            </div>
          )}

          {/* Email Sign In Form */}
          {(authMode === 'signin' || authMode === 'signup') && (
            <form onSubmit={handleEmailAuth} className="space-y-4">
              {authMode === 'signup' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={authForm.name}
                    onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your full name"
                    required
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={authForm.password}
                    onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
                    placeholder={authMode === 'signup' ? 'Create a password (6+ characters)' : 'Enter your password'}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    <Lock className="h-4 w-4 text-gray-400" />
                  </button>
                </div>
              </div>

              {authMode === 'signup' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirm Password
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={authForm.confirmPassword}
                    onChange={(e) => setAuthForm({ ...authForm, confirmPassword: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Confirm your password"
                    required
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={authInProgress}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
              >
                {authInProgress ? 'Processing...' : (authMode === 'signup' ? 'Create Account & Join Team' : 'Sign In & Join Team')}
              </button>

              {authMode === 'signin' && (
                <div className="text-center">
                  <button
                    type="button"
                    onClick={handleForgotPassword}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Forgot your password?
                  </button>
                </div>
              )}

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setAuthMode('choose')}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  ← Back to sign-in options
                </button>
              </div>

              {authMode === 'signin' && (
                <div className="text-center">
                  <p className="text-sm text-gray-500">
                    Don't have an account?{' '}
                    <button
                      type="button"
                      onClick={() => setAuthMode('signup')}
                      className="font-medium text-blue-600 hover:text-blue-500"
                    >
                      Sign up here
                    </button>
                  </p>
                </div>
              )}

              {authMode === 'signup' && (
                <div className="text-center">
                  <p className="text-sm text-gray-500">
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={() => setAuthMode('signin')}
                      className="font-medium text-blue-600 hover:text-blue-500"
                    >
                      Sign in here
                    </button>
                  </p>
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>Invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  )
} 