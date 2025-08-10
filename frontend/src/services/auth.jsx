import React, { createContext, useContext, useEffect, useState } from 'react'
import { initializeApp } from 'firebase/app'
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  OAuthProvider,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
  updateProfile,
  signOut,
  onAuthStateChanged
} from 'firebase/auth'

const firebaseConfig = {
  // Add your Firebase config here
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
}

const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

// Export auth instance and helper functions for use outside React components
export { auth }

export const getCurrentUser = () => {
  return auth.currentUser
}

export const getIdToken = async () => {
  const user = getCurrentUser()
  if (user) {
    return await user.getIdToken()
  }
  return null
}

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [userProfile, setUserProfile] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [needsProfileSetup, setNeedsProfileSetup] = useState(false)

  // Sign in with Google
  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider()
    try {
      const result = await signInWithPopup(auth, provider)
      return result.user
    } catch (error) {
      console.error('Google sign in error:', error)
      throw error
    }
  }

  // Sign in with Apple
  const signInWithApple = async () => {
    const provider = new OAuthProvider('apple.com')
    try {
      const result = await signInWithPopup(auth, provider)
      return result.user
    } catch (error) {
      console.error('Apple sign in error:', error)
      throw error
    }
  }

  // Sign in with Microsoft (Outlook)
  const signInWithMicrosoft = async () => {
    const provider = new OAuthProvider('microsoft.com')
    try {
      const result = await signInWithPopup(auth, provider)
      return result.user
    } catch (error) {
      console.error('Microsoft sign in error:', error)
      throw error
    }
  }

  // Sign up with email and password
  const signUpWithEmail = async (email, password, displayName) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update display name if provided
      if (displayName && result.user) {
        await updateProfile(result.user, { displayName })
      }
      
      return result.user
    } catch (error) {
      console.error('Email signup error:', error)
      throw error
    }
  }

  // Sign in with email and password
  const signInWithEmail = async (email, password) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      return result.user
    } catch (error) {
      console.error('Email sign in error:', error)
      throw error
    }
  }

  // Reset password
  const resetPassword = async (email) => {
    try {
      await sendPasswordResetEmail(auth, email)
      return { success: true }
    } catch (error) {
      console.error('Password reset error:', error)
      throw error
    }
  }

  // Sign out
  const logout = async () => {
    try {
      await signOut(auth)
      setUserProfile(null)
      setNeedsProfileSetup(false)
    } catch (error) {
      console.error('Sign out error:', error)
      throw error
    }
  }

  // Get ID token for API requests
  const getIdToken = async () => {
    if (user) {
      return await user.getIdToken()
    }
    return null
  }

  // Setup user profile after first login
  const setupUserProfile = async (profileData) => {
    try {
      setProfileLoading(true)
      const { api } = await import('./api')
      
      const setupData = {
        email: user.email,
        name: profileData.name || user.displayName,
        phone: profileData.phone,
        company_name: profileData.company_name,
        settings: profileData.settings || {}
      }
      
      const result = await api.setupUserProfile(setupData)
      if (result.success) {
        setUserProfile(result.user)
        setNeedsProfileSetup(false)
        return result
      } else {
        throw new Error(result.error || 'Profile setup failed')
      }
    } catch (error) {
      console.error('Profile setup error:', error)
      throw error
    } finally {
      setProfileLoading(false)
    }
  }

  // Load user profile
  const loadUserProfile = async () => {
    try {
      console.log('loadUserProfile: Starting to load profile...')
      setProfileLoading(true)
      const { api } = await import('./api')
      const result = await api.getUserProfile()
      
      console.log('loadUserProfile: API result:', result)
      
      if (result.success) {
        console.log('loadUserProfile: Setting user profile:', result.user)
        setUserProfile(result.user)
        setNeedsProfileSetup(false)
      } else {
        // User exists in Firebase but not in our database - needs profile setup
        if (result.error && result.error.includes('not found')) {
          console.log('loadUserProfile: User not found, needs profile setup')
          setNeedsProfileSetup(true)
        } else {
          console.error('Failed to load user profile:', result.error)
        }
      }
    } catch (error) {
      console.error('Error loading user profile:', error)
      // If user is authenticated but profile fails to load, they likely need setup
      setNeedsProfileSetup(true)
    } finally {
      setProfileLoading(false)
    }
  }

  // Refresh user profile
  const refreshUserProfile = async () => {
    if (user) {
      await loadUserProfile()
    }
  }

  // Update user profile
  const updateUserProfile = async (updateData) => {
    try {
      setProfileLoading(true)
      // Note: This would require an update endpoint in the backend
      // For now, we'll just refresh the profile
      await refreshUserProfile()
      return { success: true }
    } catch (error) {
      console.error('Error updating user profile:', error)
      throw error
    } finally {
      setProfileLoading(false)
    }
  }

  // Check if user is fully set up (authenticated + profile complete)
  const isUserSetup = () => {
    return !!(user && userProfile && !needsProfileSetup)
  }

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser)
      
      if (firebaseUser) {
        // TEMP: Log Firebase UID to console for debugging
        console.log('FIREBASE UID:', firebaseUser.uid)
        // User is authenticated, now check if they have a profile in our system
        await loadUserProfile()
      } else {
        // Check if user is authenticated via OTC
        const otcUser = getOTCUser()
        if (otcUser) {
          setUserProfile(otcUser)
          setNeedsProfileSetup(false)
        } else {
          // User signed out
          setUserProfile(null)
          setNeedsProfileSetup(false)
        }
      }
      
      setLoading(false)
    })

    return unsubscribe
  }, [])

  // OTC Authentication methods
  const signInWithOTC = async (phoneNumber, code) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/sms-auth/login/verify-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phone_number: phoneNumber,
          code: code 
        })
      })

      const result = await response.json()
      
      if (result.success) {
        // Store OTC user info
        localStorage.setItem('otc_user', JSON.stringify(result.user))
        localStorage.setItem('otc_token', result.token)
        return result
      } else {
        throw new Error(result.error || 'OTC authentication failed')
      }
    } catch (error) {
      console.error('OTC sign in error:', error)
      throw error
    }
  }

  const logoutOTC = () => {
    localStorage.removeItem('otc_user')
    localStorage.removeItem('otc_token')
    setUserProfile(null)
    setNeedsProfileSetup(false)
  }

  const getOTCToken = () => {
    return localStorage.getItem('otc_token')
  }

  const getOTCUser = () => {
    const userStr = localStorage.getItem('otc_user')
    return userStr ? JSON.parse(userStr) : null
  }

  const isOTCAuthenticated = () => {
    return !!getOTCToken()
  }

  const value = {
    // Auth state
    user,
    loading,
    userProfile,
    profileLoading,
    needsProfileSetup,
    
    // Auth methods
    signInWithGoogle,
    signInWithApple,
    signInWithMicrosoft,
    signUpWithEmail,
    signInWithEmail,
    resetPassword,
    logout,
    getIdToken,
    
    // OTC Auth methods
    signInWithOTC,
    logoutOTC,
    getOTCToken,
    getOTCUser,
    isOTCAuthenticated,
    
    // Profile methods
    setupUserProfile,
    loadUserProfile,
    refreshUserProfile,
    updateUserProfile,
    
    // Helper methods
    isUserSetup
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 