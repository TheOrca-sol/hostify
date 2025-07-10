import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { LogOut, Upload, Home, User, FileText } from 'lucide-react'

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  if (!user) {
    return null
  }

  return (
    <nav className="bg-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <div className="bg-primary-600 text-white p-2 rounded-lg">
              <Home size={20} />
            </div>
            <span className="text-xl font-bold text-gray-800">Hostify</span>
          </Link>

          <div className="flex items-center space-x-4">
            <Link
              to="/"
              className="flex items-center space-x-1 text-gray-700 hover:text-primary-600 transition-colors"
            >
              <Home size={18} />
              <span>Dashboard</span>
            </Link>
            
            <Link
              to="/contract-templates"
              className="flex items-center space-x-1 text-gray-700 hover:text-primary-600 transition-colors"
            >
              <FileText size={18} />
              <span>Contract Templates</span>
            </Link>

            <div className="flex items-center space-x-3 border-l pl-4">
              <div className="flex items-center space-x-2">
                <User size={18} className="text-gray-600" />
                <span className="text-sm text-gray-700">
                  {user.displayName || user.email}
                </span>
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 text-gray-700 hover:text-red-600 transition-colors"
              >
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar 