import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './services/auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ProfileSetup from './pages/ProfileSetup'
import Navbar from './components/Navbar'
import { Toaster } from './components/Toaster'
import GuestVerification from './pages/GuestVerification'
import ContractTemplates from './pages/ContractTemplates'
import ContractSigning from './components/ContractSigning'

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
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
            
            {/* Protected Routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Navbar />
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/profile/setup" element={
              <ProtectedRoute>
                <ProfileSetup />
              </ProtectedRoute>
            } />
            
            <Route path="/contract-templates" element={
              <ProtectedRoute>
                <Navbar />
                <ContractTemplates />
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
          </Routes>
          
          <Toaster />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App 