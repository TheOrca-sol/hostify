import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
  Plus, 
  Users, 
  Building, 
  BarChart3,
  MoreVertical,
  Edit,
  Trash2,
  UserPlus,
  ArrowRight,
  Eye
} from 'lucide-react';

const TeamsManagement = () => {
  const [teams, setTeams] = useState({ owned_teams: [], member_teams: [] });
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [performanceData, setPerformanceData] = useState({});
  const [properties, setProperties] = useState([]);

  // Load teams and properties on component mount
  useEffect(() => {
    loadTeams();
    loadProperties();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const response = await api.getTeams();
      if (response.success) {
        setTeams(response);
        
        // Load performance data for each owned team
        const performancePromises = response.owned_teams.map(async (team) => {
          const perfResponse = await api.getTeamPerformance(team.id);
          return { teamId: team.id, data: perfResponse };
        });
        
        const performanceResults = await Promise.all(performancePromises);
        const performanceMap = {};
        performanceResults.forEach(({ teamId, data }) => {
          if (data.success) {
            performanceMap[teamId] = data.metrics;
          }
        });
        setPerformanceData(performanceMap);
      } else {
        toast.error(response.error || 'Failed to load teams');
      }
    } catch (error) {
      console.error('Error loading teams:', error);
      toast.error('Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const response = await api.getProperties();
      if (response.success) {
        setProperties(response.properties || []);
      }
    } catch (error) {
      console.error('Error loading properties:', error);
    }
  };

  const handleCreateTeam = async (teamData) => {
    try {
      const response = await api.createTeam(teamData);
      if (response.success) {
        toast.success('Team created successfully!');
        setShowCreateModal(false);
        loadTeams();
      } else {
        toast.error(response.error || 'Failed to create team');
      }
    } catch (error) {
      console.error('Error creating team:', error);
      toast.error('Failed to create team');
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (!confirm('Are you sure you want to delete this team? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await api.deleteTeam(teamId);
      if (response.success) {
        toast.success('Team deleted successfully');
        loadTeams();
      } else {
        toast.error(response.error || 'Failed to delete team');
      }
    } catch (error) {
      console.error('Error deleting team:', error);
      toast.error('Failed to delete team');
    }
  };

  const getTeamIcon = (teamName) => {
    const name = teamName.toLowerCase();
    if (name.includes('hotel')) return '🏨';
    if (name.includes('apartment')) return '🏠';
    if (name.includes('villa')) return '🏖️';
    if (name.includes('clean')) return '🧹';
    if (name.includes('maintenance')) return '🔧';
    return '👥';
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'manager': return 'bg-blue-100 text-blue-800';
      case 'cleaner': return 'bg-green-100 text-green-800';
      case 'maintenance': return 'bg-orange-100 text-orange-800';
      case 'assistant': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatMetric = (value, type) => {
    if (value === null || value === undefined) return 'N/A';
    
    switch (type) {
      case 'percentage':
        return `${Math.round(value)}%`;
      case 'currency':
        return `$${value.toLocaleString()}`;
      case 'time':
        return `${Math.round(value)}min`;
      default:
        return Math.round(value).toLocaleString();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Teams Management</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage your organization teams and track their performance
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Team
            </button>
          </div>
        </div>

        {/* Performance Overview */}
        {teams.owned_teams.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Organization Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Teams</p>
                    <p className="text-2xl font-semibold text-gray-900">{teams.owned_teams.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Building className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Properties</p>
                    <p className="text-2xl font-semibold text-gray-900">{properties.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart3 className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Avg Performance</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {formatMetric(
                        Object.values(performanceData).reduce((sum, metrics) => sum + (metrics?.efficiency_score || 0), 0) / 
                        Math.max(Object.keys(performanceData).length, 1), 
                        'percentage'
                      )}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <span className="text-2xl">💰</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {formatMetric(
                        Object.values(performanceData).reduce((sum, metrics) => sum + (metrics?.revenue || 0), 0),
                        'currency'
                      )}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Owned Teams */}
        {teams.owned_teams.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Your Teams</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {teams.owned_teams.map((team) => (
                <TeamCard 
                  key={team.id} 
                  team={team} 
                  isOwner={true}
                  performance={performanceData[team.id]}
                  onDelete={() => handleDeleteTeam(team.id)}
                  onInvite={() => {
                    setSelectedTeam(team);
                    setShowInviteModal(true);
                  }}
                  getTeamIcon={getTeamIcon}
                  formatMetric={formatMetric}
                />
              ))}
            </div>
          </div>
        )}

        {/* Member Teams */}
        {teams.member_teams.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Teams You're In</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {teams.member_teams.map((team) => (
                <TeamCard 
                  key={team.id} 
                  team={team} 
                  isOwner={false}
                  userRole={team.user_role}
                  getTeamIcon={getTeamIcon}
                  getRoleColor={getRoleColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {teams.owned_teams.length === 0 && teams.member_teams.length === 0 && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No teams</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating your first team.</p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Team
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateModal && (
        <CreateTeamModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateTeam}
        />
      )}

      {/* Invite Member Modal */}
      {showInviteModal && selectedTeam && (
        <InviteMemberModal
          team={selectedTeam}
          onClose={() => {
            setShowInviteModal(false);
            setSelectedTeam(null);
          }}
          onSubmit={async (memberData) => {
            try {
              const response = await api.inviteTeamMemberNew(selectedTeam.id, memberData);
              if (response.success) {
                toast.success('Team member invited successfully!');
                setShowInviteModal(false);
                setSelectedTeam(null);
              } else {
                toast.error(response.error || 'Failed to invite team member');
              }
            } catch (error) {
              console.error('Error inviting team member:', error);
              toast.error('Failed to invite team member');
            }
          }}
        />
      )}
    </div>
  );
};

// Team Card Component
const TeamCard = ({ team, isOwner, userRole, performance, onDelete, onInvite, getTeamIcon, formatMetric, getRoleColor }) => {
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Team Header */}
      <div 
        className="p-4"
        style={{ 
          background: team.color ? `linear-gradient(135deg, ${team.color}20, ${team.color}40)` : 'linear-gradient(135deg, #f3f4f6, #e5e7eb)',
          borderLeft: `4px solid ${team.color || '#6b7280'}`
        }}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{getTeamIcon(team.name)}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
              {team.description && (
                <p className="text-sm text-gray-600 mt-1">{team.description}</p>
              )}
            </div>
          </div>
          
          {isOwner && (
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="p-1 rounded-full hover:bg-white hover:bg-opacity-50"
              >
                <MoreVertical className="h-5 w-5 text-gray-600" />
              </button>
              
              {showDropdown && (
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg z-10 border">
                  <div className="py-1">
                    <button
                      onClick={() => {
                        onInvite();
                        setShowDropdown(false);
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <UserPlus className="h-4 w-4 mr-2" />
                      Invite Member
                    </button>
                    <button
                      onClick={() => {
                        onDelete();
                        setShowDropdown(false);
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Team
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Team Stats */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{team.properties_count || 0}</p>
            <p className="text-xs text-gray-500">Properties</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{team.members_count || 0}</p>
            <p className="text-xs text-gray-500">Members</p>
          </div>
        </div>

        {/* Performance Metrics (for owned teams) */}
        {isOwner && performance && (
          <div className="border-t pt-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-gray-500">Completion Rate</p>
                <p className="font-semibold">{formatMetric(performance.task_completion_rate, 'percentage')}</p>
              </div>
              <div>
                <p className="text-gray-500">Guest Satisfaction</p>
                <p className="font-semibold">{formatMetric(performance.guest_satisfaction, 'percentage')}</p>
              </div>
              <div>
                <p className="text-gray-500">Response Time</p>
                <p className="font-semibold">{formatMetric(performance.average_response_time, 'time')}</p>
              </div>
              <div>
                <p className="text-gray-500">Revenue</p>
                <p className="font-semibold">{formatMetric(performance.revenue, 'currency')}</p>
              </div>
            </div>
          </div>
        )}

        {/* User Role (for member teams) */}
        {!isOwner && userRole && (
          <div className="border-t pt-4">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(userRole)}`}>
              Your Role: {userRole.charAt(0).toUpperCase() + userRole.slice(1)}
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center mt-4 pt-4 border-t">
          <Link
            to={`/teams/${team.id}`}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View Details
          </Link>
          
          {isOwner && (
            <button
              onClick={onInvite}
              className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <UserPlus className="h-4 w-4 mr-1" />
              Invite
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Create Team Modal Component
const CreateTeamModal = ({ onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#4ECDC4'
  });

  const teamColors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Team name is required');
      return;
    }
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Team</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Team Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Hotel Team, Cleaning Services"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Description (Optional)</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Brief description of the team's responsibilities"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Team Color</label>
              <div className="flex flex-wrap gap-2">
                {teamColors.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, color }))}
                    className={`w-8 h-8 rounded-full border-2 ${
                      formData.color === color ? 'border-gray-900' : 'border-gray-300'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            
            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                Create Team
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Invite Member Modal Component
const InviteMemberModal = ({ team, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    invitation_method: 'email',
    role: 'cleaner'
  });

  const roles = [
    { value: 'manager', label: 'Manager', description: 'Can manage team and invite members' },
    { value: 'cleaner', label: 'Cleaner', description: 'Handles cleaning tasks and reporting' },
    { value: 'maintenance', label: 'Maintenance', description: 'Handles maintenance and repairs' },
    { value: 'assistant', label: 'Assistant', description: 'Provides guest support and basic tasks' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (formData.invitation_method === 'email' && !formData.email.trim()) {
      toast.error('Email is required for email invitations');
      return;
    }
    
    if (formData.invitation_method === 'sms' && !formData.phone.trim()) {
      toast.error('Phone number is required for SMS invitations');
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Invite Member to {team.name}
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Invitation Method</label>
              <select
                value={formData.invitation_method}
                onChange={(e) => setFormData(prev => ({ ...prev, invitation_method: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
              </select>
            </div>
            
            {formData.invitation_method === 'email' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="member@example.com"
                  required
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="+212123456789"
                  required
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {roles.find(r => r.value === formData.role)?.description}
              </p>
            </div>
            
            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                Send Invitation
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TeamsManagement;
