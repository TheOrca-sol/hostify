import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Users, Plus, Trash2, Mail, Crown, User, Wrench, Sparkles, Eye } from 'lucide-react'
import { toast } from './Toaster'

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

export default function TeamManagement({ property, canManageTeam = true }) {
  const [teamMembers, setTeamMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'cohost'
  })
  const [inviting, setInviting] = useState(false)

  useEffect(() => {
    if (property?.id) {
      loadTeamMembers()
    }
  }, [property?.id])

  const loadTeamMembers = async () => {
    try {
      setLoading(true)
      const result = await api.getPropertyTeamMembers(property.id)
      if (result.success) {
        setTeamMembers(result.team_members || [])
      } else {
        console.error('Failed to load team members:', result.error)
      }
    } catch (error) {
      console.error('Error loading team members:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    
    if (!inviteForm.email || !inviteForm.role) {
      toast.error('Please fill in all fields')
      return
    }

    try {
      setInviting(true)
      const result = await api.inviteTeamMember(property.id, {
        email: inviteForm.email,
        role: inviteForm.role
      })

      if (result.success) {
        toast.success(`Invitation sent to ${inviteForm.email}`)
        setInviteForm({ email: '', role: 'cohost' })
        setShowInviteForm(false)
        loadTeamMembers() // Refresh the list
      } else {
        toast.error(result.error || 'Failed to send invitation')
      }
    } catch (error) {
      toast.error('Failed to send invitation')
    } finally {
      setInviting(false)
    }
  }

  const handleRemoveMember = async (member) => {
    if (!confirm(`Are you sure you want to remove ${member.user_name} from this property team?`)) {
      return
    }

    try {
      const result = await api.removeTeamMember(property.id, member.user_id)
      if (result.success) {
        toast.success('Team member removed successfully')
        loadTeamMembers()
      } else {
        toast.error(result.error || 'Failed to remove team member')
      }
    } catch (error) {
      toast.error('Failed to remove team member')
    }
  }

  const getRoleConfig = (role) => ROLE_CONFIG[role] || ROLE_CONFIG.assistant

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Team Management</h3>
        {canManageTeam && (
          <button
            onClick={() => setShowInviteForm(true)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Invite Member
          </button>
        )}
      </div>

      {/* Current Team Members */}
      <div className="space-y-4">
        {teamMembers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No team members yet</p>
            {canManageTeam && (
              <p className="text-sm">Invite your first team member to get started</p>
            )}
          </div>
        ) : (
          teamMembers.map((member) => {
            const roleConfig = getRoleConfig(member.role)
            const RoleIcon = roleConfig.icon

            return (
              <div key={member.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-full bg-${roleConfig.color}-100`}>
                    <RoleIcon className={`w-5 h-5 text-${roleConfig.color}-600`} />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{member.user_name}</h4>
                    <p className="text-sm text-gray-500">{member.user_email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${roleConfig.color}-100 text-${roleConfig.color}-800`}>
                        {roleConfig.label}
                      </span>
                      <span className="text-xs text-gray-400">
                        Invited by {member.invited_by_name}
                      </span>
                    </div>
                  </div>
                </div>
                {canManageTeam && (
                  <button
                    onClick={() => handleRemoveMember(member)}
                    className="text-gray-400 hover:text-red-600 focus:outline-none"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Invite Form Modal */}
      {showInviteForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Invite Team Member
              </h3>
              
              <form onSubmit={handleInvite} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteForm.email}
                    onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter email address"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={inviteForm.role}
                    onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(ROLE_CONFIG).map(([role, config]) => (
                      <option key={role} value={role}>
                        {config.label} - {config.description}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowInviteForm(false)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviting}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {inviting ? (
                      <>
                        <Mail className="animate-spin w-4 h-4 mr-2" />
                        Sending...
                      </>
                    ) : (
                      'Send Invitation'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 