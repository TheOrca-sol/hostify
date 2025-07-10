import React, { createContext, useContext, useEffect, useState } from 'react'
import { initializeApp } from 'firebase/app'
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  OAuthProvider,
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
      setProfileLoading(true)
      const { api } = await import('./api')
      const result = await api.getUserProfile()
      
      if (result.success) {
        setUserProfile(result.user)
        setNeedsProfileSetup(false)
      } else {
        // User exists in Firebase but not in our database - needs profile setup
        if (result.error && result.error.includes('not found')) {
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
        // User is authenticated, now check if they have a profile in our system
        await loadUserProfile()
      } else {
        // User signed out
        setUserProfile(null)
        setNeedsProfileSetup(false)
      }
      
      setLoading(false)
    })

    return unsubscribe
  }, [])

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
    logout,
    getIdToken,
    
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