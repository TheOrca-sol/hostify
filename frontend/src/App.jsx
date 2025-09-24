import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './services/auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ProfileSetup from './pages/ProfileSetup'
import Profile from './pages/Profile'
import Navbar from './components/Navbar'
import { Toaster } from './components/Toaster'
import GuestVerification from './pages/GuestVerification'
import ContractTemplates from './pages/ContractTemplates'
import MessageTemplates from './pages/MessageTemplates'
import ContractSigning from './components/ContractSigning'
import ContractSignedSuccess from './pages/ContractSignedSuccess'
import InvitationAcceptance from './pages/InvitationAcceptance'
import TeamDetails from './pages/TeamDetails'
import SmartLocks from './pages/SmartLocks'

// Protected route wrapper
const ProtectedRoute = ({ children, allowProfileSetup = false }) => {
  const { user, loading, needsProfileSetup } = useAuth()
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" />
  }
  
  // If user needs profile setup and we're not on the profile setup page
  if (needsProfileSetup && !allowProfileSetup) {
    return <Navigate to="/profile-setup" />
  }
  
  return children
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/verify/:token" element={<GuestVerification />} />
            <Route path="/contract/sign/:token" element={<ContractSigning mode="sign" />} />
            <Route path="/contract-signed-success" element={<ContractSignedSuccess />} />
            <Route path="/invite/:token" element={<InvitationAcceptance />} />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Navbar />
                <Dashboard />
              </ProtectedRoute>
            } />

            <Route path="/" element={
              <ProtectedRoute>
                <Navbar />
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/profile/setup" element={
              <ProtectedRoute allowProfileSetup={true}>
                <ProfileSetup />
              </ProtectedRoute>
            } />
            
                    <Route path="/profile" element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        } />
        
        <Route path="/profile-setup" element={
          <ProtectedRoute allowProfileSetup={true}>
            <ProfileSetup />
          </ProtectedRoute>
        } />
            
            <Route path="/contract-templates" element={
              <ProtectedRoute>
                <Navbar />
                <ContractTemplates />
              </ProtectedRoute>
            } />

            <Route path="/message-templates" element={
              <ProtectedRoute>
                <Navbar />
                <MessageTemplates />
              </ProtectedRoute>
            } />

            <Route path="/teams/:teamId" element={
              <ProtectedRoute>
                <Navbar />
                <TeamDetails />
              </ProtectedRoute>
            } />
            
            {/* Contract Routes */}
            <Route path="/contracts/:contractId" element={
              <ProtectedRoute>
                <Navbar />
                <div className="container mx-auto px-4 py-8">
                  <ContractSigning mode="view" />
                </div>
              </ProtectedRoute>
            } />
            
            <Route path="/contracts/:contractId/sign" element={
              <ProtectedRoute>
                <Navbar />
                <div className="container mx-auto px-4 py-8">
                  <ContractSigning mode="sign" />
                </div>
              </ProtectedRoute>
            } />

            <Route path="/smart-locks" element={
              <ProtectedRoute>
                <Navbar />
                <SmartLocks />
              </ProtectedRoute>
            } />
          </Routes>
          
          <Toaster />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App 