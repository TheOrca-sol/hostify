import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { 
  Home,
  FileText,
  MessageSquare,
  LogOut,
  User
} from 'lucide-react'

export default function Navbar() {
  const { user, signOut } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold text-blue-600">
              Hostify
            </Link>

            <div className="hidden md:flex items-center space-x-4">
              <Link
                to="/"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                  isActive('/') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Home size={20} />
                <span>Dashboard</span>
              </Link>

              <Link
                to="/contract-templates"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                  isActive('/contract-templates') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FileText size={20} />
                <span>Contracts</span>
              </Link>

              <Link
                to="/message-templates"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                  isActive('/message-templates') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <MessageSquare size={20} />
                <span>Messages</span>
              </Link>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              to="/profile-setup"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                isActive('/profile-setup') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <User size={20} />
              <span className="hidden md:inline">{user?.email}</span>
            </Link>

            <button
              onClick={signOut}
              className="flex items-center space-x-2 px-3 py-2 rounded-md text-gray-600 hover:bg-gray-100"
            >
              <LogOut size={20} />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
} 