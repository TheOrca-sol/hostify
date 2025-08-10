import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Users, Plus, Search, Filter, Crown, User, Wrench, Sparkles, Eye, Building, Mail, Trash2, Phone, MessageSquare } from 'lucide-react'
import PhoneInput from '../components/PhoneInput'
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

export default function TeamManagement() {
  const [properties, setProperties] = useState([])
  const [selectedProperty, setSelectedProperty] = useState('all')
  const [teamData, setTeamData] = useState({})
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteForm, setInviteForm] = useState({
    propertyId: 'all',
    email: '',
    phone: '',
    invitationMethod: 'email', // 'email' or 'sms'
    role: 'cohost'
  })
  const [inviting, setInviting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedProperty !== 'all') {
      loadTeamMembers(selectedProperty)
    } else {
      loadAllTeamMembers()
    }
  }, [selectedProperty])

  const loadData = async () => {
    try {
      setLoading(true)
      // Load properties first
      const propertiesResult = await api.getProperties()
      if (propertiesResult.success) {
        const userProperties = propertiesResult.properties.filter(
          p => p.relationship_type === 'owner' || 
          (p.permissions && p.permissions.invite_team_members)
        )
        setProperties(userProperties)
        
        // Load team data for all properties
        await loadTeamMembersForProperties(userProperties)
      }
    } catch (error) {
      console.error('Error loading data:', error)
      toast.error('Failed to load team data')
    } finally {
      setLoading(false)
    }
  }

  const loadTeamMembersForProperties = async (propertiesToLoad) => {
    try {
      const teamDataTemp = {}
      
      for (const property of propertiesToLoad) {
        const result = await api.getPropertyTeamMembers(property.id)
        if (result.success) {
          teamDataTemp[property.id] = result.team_members || []
        }
      }
      
      setTeamData(teamDataTemp)
    } catch (error) {
      console.error('Error loading team members:', error)
    }
  }

  const loadAllTeamMembers = async () => {
    await loadTeamMembersForProperties(properties)
  }

  const loadTeamMembers = async (propertyId) => {
    try {
      const result = await api.getPropertyTeamMembers(propertyId)
      if (result.success) {
        setTeamData({ [propertyId]: result.team_members || [] })
      }
    } catch (error) {
      console.error('Error loading team members:', error)
    }
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    
    // Validation - check appropriate field based on invitation method
    const contactInfo = inviteForm.invitationMethod === 'email' ? inviteForm.email : inviteForm.phone
    
    if (!inviteForm.propertyId || !contactInfo || !inviteForm.role) {
      toast.error('Please fill in all fields')
      return
    }

    try {
      setInviting(true)
      
      if (inviteForm.propertyId === 'all') {
        // Invite to all properties owned by the user
        const ownedProperties = properties.filter(p => p.relationship_type === 'owner')
        
        if (ownedProperties.length === 0) {
          toast.error('No properties found to invite to')
          return
        }

        let successCount = 0
        let errors = []

        // Send invitations to all properties
        for (const property of ownedProperties) {
          try {
            // Prepare invitation data based on method
            const invitationData = {
              role: inviteForm.role,
              invitation_method: inviteForm.invitationMethod
            }
            
            if (inviteForm.invitationMethod === 'email') {
              invitationData.email = inviteForm.email
            } else {
              invitationData.phone = inviteForm.phone
            }
            
            const result = await api.inviteTeamMember(property.id, invitationData)
            
            if (result.success) {
              successCount++
            } else {
              errors.push(`${property.name}: ${result.error}`)
            }
          } catch (error) {
            errors.push(`${property.name}: Failed to send invitation`)
          }
        }

        if (successCount === ownedProperties.length) {
          const methodIcon = inviteForm.invitationMethod === 'email' ? '📧' : '📱'
          toast.success(`✅ ${methodIcon} ${contactInfo} invited to all ${successCount} properties`)
        } else if (successCount > 0) {
          const methodIcon = inviteForm.invitationMethod === 'email' ? '📧' : '📱'
          toast.success(`✅ ${methodIcon} ${contactInfo} invited to ${successCount}/${ownedProperties.length} properties`)
          if (errors.length > 0) {
            console.warn('Some invitations failed:', errors)
          }
        } else {
          toast.error('Failed to send invitations to any properties')
        }
      } else {
        // Invite to specific property
        // Prepare invitation data based on method
        const invitationData = {
          role: inviteForm.role,
          invitation_method: inviteForm.invitationMethod
        }
        
        if (inviteForm.invitationMethod === 'email') {
          invitationData.email = inviteForm.email
        } else {
          invitationData.phone = inviteForm.phone
        }
        
        const result = await api.inviteTeamMember(inviteForm.propertyId, invitationData)

        if (result.success) {
          const methodIcon = inviteForm.invitationMethod === 'email' ? '📧' : '📱'
          toast.success(`✅ ${methodIcon} Invitation sent to ${contactInfo}`)
        } else {
          toast.error(result.error || 'Failed to send invitation')
          return
        }
      }

      // Reset form and close modal
      setInviteForm({ propertyId: 'all', email: '', phone: '', invitationMethod: 'email', role: 'cohost' })
      setShowInviteModal(false)
      
      // Refresh team data
      if (selectedProperty !== 'all') {
        loadTeamMembers(selectedProperty)
      } else {
        loadAllTeamMembers()
      }
      
    } catch (error) {
      console.error('Error inviting team member:', error)
      toast.error('Failed to send invitation')
    } finally {
      setInviting(false)
    }
  }

  const handleRemoveMember = async (propertyId, member) => {
    if (!confirm(`Are you sure you want to remove ${member.user_name} from this property team?`)) {
      return
    }

    try {
      const result = await api.removeTeamMember(propertyId, member.user_id)
      if (result.success) {
        toast.success('Team member removed successfully')
        
        // Refresh team data
        if (selectedProperty !== 'all') {
          loadTeamMembers(selectedProperty)
        } else {
          loadAllTeamMembers()
        }
      } else {
        toast.error(result.error || 'Failed to remove team member')
      }
    } catch (error) {
      toast.error('Failed to remove team member')
    }
  }

  const getFilteredTeamMembers = () => {
    let allMembers = []
    
    // Collect all team members from selected properties
    const propertiesToShow = selectedProperty === 'all' 
      ? properties 
      : properties.filter(p => p.id === selectedProperty)
    
    propertiesToShow.forEach(property => {
      const members = teamData[property.id] || []
      members.forEach(member => {
        allMembers.push({
          ...member,
          property_name: property.name,
          property_id: property.id
        })
      })
    })

    // Apply filters
    if (searchTerm) {
      allMembers = allMembers.filter(member =>
        member.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        member.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        member.property_name?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (roleFilter !== 'all') {
      allMembers = allMembers.filter(member => member.role === roleFilter)
    }

    return allMembers
  }

  const getRoleConfig = (role) => ROLE_CONFIG[role] || ROLE_CONFIG.assistant

  const getTotalMembersByRole = () => {
    const allMembers = getFilteredTeamMembers()
    const counts = {}
    
    Object.keys(ROLE_CONFIG).forEach(role => {
      counts[role] = allMembers.filter(m => m.role === role).length
    })
    
    return counts
  }

  const filteredMembers = getFilteredTeamMembers()
  const roleCounts = getTotalMembersByRole()

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1">
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
            <div className="lg:col-span-3">
              <div className="space-y-4">
                <div className="h-16 bg-gray-200 rounded"></div>
                <div className="h-16 bg-gray-200 rounded"></div>
                <div className="h-16 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Team Management</h1>
          <p className="mt-1 text-gray-600">
            Manage your team members across all properties
          </p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          Invite Member
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar - Filters and Stats */}
        <div className="lg:col-span-1">
          <div className="space-y-6">
            {/* Property Filter */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Filter by Property</h3>
              <select
                value={selectedProperty}
                onChange={(e) => setSelectedProperty(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Properties</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>
                    {property.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Role Stats */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Team by Role</h3>
              <div className="space-y-3">
                {Object.entries(ROLE_CONFIG).map(([role, config]) => {
                  const RoleIcon = config.icon
                  const count = roleCounts[role] || 0
                  
                  return (
                    <div 
                      key={role}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                        roleFilter === role ? `bg-${config.color}-50 border border-${config.color}-200` : 'hover:bg-gray-50'
                      }`}
                      onClick={() => setRoleFilter(roleFilter === role ? 'all' : role)}
                    >
                      <div className="flex items-center space-x-2">
                        <RoleIcon className={`w-4 h-4 text-${config.color}-600`} />
                        <span className="text-sm font-medium text-gray-900">{config.label}</span>
                      </div>
                      <span className={`text-sm font-semibold ${count > 0 ? `text-${config.color}-600` : 'text-gray-400'}`}>
                        {count}
                      </span>
                    </div>
                  )
                })}
              </div>
              
              {roleFilter !== 'all' && (
                <button
                  onClick={() => setRoleFilter('all')}
                  className="mt-3 w-full text-sm text-blue-600 hover:text-blue-800"
                >
                  Clear filter
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Search Bar */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search team members, emails, or properties..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Team Members List */}
          <div className="bg-white rounded-lg border border-gray-200">
            {filteredMembers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No team members found</h3>
                <p className="text-gray-600 mb-4">
                  {searchTerm || roleFilter !== 'all' 
                    ? 'Try adjusting your search or filter criteria' 
                    : 'Start building your team by inviting members to your properties'
                  }
                </p>
                {(!searchTerm && roleFilter === 'all') && (
                  <button
                    onClick={() => setShowInviteModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Invite First Member
                  </button>
                )}
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredMembers.map((member) => {
                  const roleConfig = getRoleConfig(member.role)
                  const RoleIcon = roleConfig.icon

                  return (
                    <div key={`${member.property_id}-${member.id}`} className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className={`p-3 rounded-full bg-${roleConfig.color}-100`}>
                            <RoleIcon className={`w-6 h-6 text-${roleConfig.color}-600`} />
                          </div>
                          <div>
                            <h4 className="text-lg font-medium text-gray-900">{member.user_name}</h4>
                            <p className="text-sm text-gray-600">{member.user_email}</p>
                            <div className="flex items-center space-x-3 mt-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${roleConfig.color}-100 text-${roleConfig.color}-800`}>
                                {roleConfig.label}
                              </span>
                              <div className="flex items-center text-xs text-gray-500">
                                <Building className="w-3 h-3 mr-1" />
                                {member.property_name}
                              </div>
                              <div className="flex items-center text-xs text-gray-500">
                                <User className="w-3 h-3 mr-1" />
                                Invited by {member.invited_by_name}
                              </div>
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveMember(member.property_id, member)}
                          className="text-gray-400 hover:text-red-600 focus:outline-none p-2"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Invite Team Member
              </h3>
              
              <form onSubmit={handleInvite} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Property
                  </label>
                  <select
                    value={inviteForm.propertyId}
                    onChange={(e) => setInviteForm({ ...inviteForm, propertyId: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="all">🏠 All Properties (Recommended for Co-hosts & Agencies)</option>
                    <option value="" disabled>--- Specific Properties ---</option>
                    {properties.map(property => (
                      <option key={property.id} value={property.id}>
                        {property.name}
                      </option>
                    ))}
                  </select>
                  
                  {inviteForm.propertyId === 'all' && (
                    <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                      <div className="flex items-start space-x-2">
                        <div className="text-blue-600 mt-0.5">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="text-sm text-blue-800">
                          <p className="font-medium">This will invite the team member to all {properties.filter(p => p.relationship_type === 'owner').length} of your properties.</p>
                          <p className="mt-1 text-blue-700">Perfect for co-hosts and agencies who help manage your entire portfolio.</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Invitation Method Selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Invitation Method
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setInviteForm({ ...inviteForm, invitationMethod: 'email', phone: '' })}
                      className={`flex items-center justify-center px-4 py-2 rounded-md border transition-colors ${
                        inviteForm.invitationMethod === 'email'
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Email
                    </button>
                    <button
                      type="button"
                      onClick={() => setInviteForm({ ...inviteForm, invitationMethod: 'sms', email: '' })}
                      className={`flex items-center justify-center px-4 py-2 rounded-md border transition-colors ${
                        inviteForm.invitationMethod === 'sms'
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      SMS
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {inviteForm.invitationMethod === 'email' 
                      ? 'Best for co-hosts and agencies' 
                      : 'Best for cleaners and maintenance workers'}
                  </p>
                </div>

                {/* Conditional Email/Phone Input */}
                {inviteForm.invitationMethod === 'email' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Mail className="h-4 w-4 text-gray-400" />
                      </div>
                      <input
                        type="email"
                        value={inviteForm.email}
                        onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                        className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter email address"
                        required
                      />
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number
                    </label>
                    <PhoneInput
                      value={inviteForm.phone}
                      onChange={(phone) => setInviteForm({ ...inviteForm, phone })}
                      placeholder="Enter phone number"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      We'll send an SMS with invitation instructions
                    </p>
                  </div>
                )}

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
                    onClick={() => setShowInviteModal(false)}
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
                        {inviteForm.propertyId === 'all' ? 'Sending to All Properties...' : 'Sending...'}
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4 mr-2" />
                        {inviteForm.propertyId === 'all' 
                          ? `Invite to All ${properties.filter(p => p.relationship_type === 'owner').length} Properties`
                          : 'Send Invitation'
                        }
                      </>
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