import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import {
  Building,
  ArrowRight,
  Check,
  X
} from 'lucide-react';

const PropertyTeamAssignment = () => {
  const [properties, setProperties] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [draggedProperty, setDraggedProperty] = useState(null);
  const [assignments, setAssignments] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [propertiesResponse, teamsResponse] = await Promise.all([
        api.getProperties(),
        api.getTeams()
      ]);

      if (propertiesResponse.success) {
        setProperties(propertiesResponse.properties || []);
        
        // Build assignments map
        const assignmentMap = {};
        propertiesResponse.properties.forEach(property => {
          if (property.team_id) {
            assignmentMap[property.id] = property.team_id;
          }
        });
        setAssignments(assignmentMap);
      }

      if (teamsResponse.success) {
        setTeams(teamsResponse.owned_teams || []);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignProperty = async (propertyId, teamId) => {
    try {
      const response = await api.assignPropertyToTeam(teamId, propertyId);
      
      if (response.success) {
        setAssignments(prev => ({ ...prev, [propertyId]: teamId }));
        toast.success('Property assigned successfully');
      } else {
        toast.error(response.error || 'Failed to assign property');
      }
    } catch (error) {
      console.error('Error assigning property:', error);
      toast.error('Failed to assign property');
    }
  };

  const handleUnassignProperty = async (propertyId) => {
    // To unassign, we would need an unassign endpoint or assign to null
    // For now, we'll show this as a placeholder
    toast.info('Unassign functionality would be implemented with an API endpoint');
  };

  const handleDragStart = (e, property) => {
    setDraggedProperty(property);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, teamId) => {
    e.preventDefault();
    
    if (draggedProperty) {
      handleAssignProperty(draggedProperty.id, teamId);
      setDraggedProperty(null);
    }
  };

  const getPropertyCountForTeam = (teamId) => {
    return Object.values(assignments).filter(id => id === teamId).length;
  };

  const getUnassignedProperties = () => {
    return properties.filter(property => !assignments[property.id]);
  };

  const getTeamColor = (team) => {
    return team.color || '#6B7280';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Property Team Assignment</h2>
          <p className="text-sm text-gray-600 mt-1">
            Drag and drop properties to assign them to teams
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unassigned Properties */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Building className="h-5 w-5 mr-2 text-gray-500" />
            Unassigned Properties ({getUnassignedProperties().length})
          </h3>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {getUnassignedProperties().length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                All properties are assigned to teams
              </p>
            ) : (
              getUnassignedProperties().map((property) => (
                <PropertyCard
                  key={property.id}
                  property={property}
                  onDragStart={handleDragStart}
                  assigned={false}
                />
              ))
            )}
          </div>
        </div>

        {/* Teams */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Teams</h3>
          
          {teams.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">No teams available</p>
              <p className="text-sm text-gray-400 mt-1">Create a team first to assign properties</p>
            </div>
          ) : (
            teams.map((team) => (
              <TeamDropZone
                key={team.id}
                team={team}
                propertyCount={getPropertyCountForTeam(team.id)}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                properties={properties.filter(p => assignments[p.id] === team.id)}
                onUnassign={handleUnassignProperty}
              />
            ))
          )}
        </div>
      </div>

      {/* Assignment Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Assignment Summary</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{properties.length}</p>
            <p className="text-sm text-gray-600">Total Properties</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {properties.length - getUnassignedProperties().length}
            </p>
            <p className="text-sm text-gray-600">Assigned</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">{getUnassignedProperties().length}</p>
            <p className="text-sm text-gray-600">Unassigned</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{teams.length}</p>
            <p className="text-sm text-gray-600">Teams</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Property Card Component
const PropertyCard = ({ property, onDragStart, assigned = false }) => {
  return (
    <div
      draggable={!assigned}
      onDragStart={(e) => onDragStart(e, property)}
      className={`p-3 border rounded-lg ${
        assigned 
          ? 'bg-gray-50 border-gray-200' 
          : 'bg-white border-gray-300 hover:border-blue-400 cursor-move'
      } transition-colors`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Building className="h-4 w-4 text-gray-400 mr-2" />
          <div>
            <p className="text-sm font-medium text-gray-900">{property.name}</p>
            {property.address && (
              <p className="text-xs text-gray-500">{property.address}</p>
            )}
          </div>
        </div>
        
        {property.team_name && (
          <div className="flex items-center">
            <span 
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white"
              style={{ backgroundColor: property.team_color || '#6B7280' }}
            >
              {property.team_name}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Team Drop Zone Component
const TeamDropZone = ({ team, propertyCount, onDragOver, onDrop, properties, onUnassign }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    setIsDragOver(false);
    onDrop(e, team.id);
  };

  return (
    <div
      onDragOver={onDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`bg-white rounded-lg shadow p-4 border-2 border-dashed transition-colors ${
        isDragOver
          ? 'border-blue-400 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <div
            className="w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: team.color || '#6B7280' }}
          ></div>
          <h4 className="text-md font-medium text-gray-900">{team.name}</h4>
        </div>
        <span className="text-sm text-gray-500">{propertyCount} properties</span>
      </div>

      {team.description && (
        <p className="text-sm text-gray-600 mb-3">{team.description}</p>
      )}

      {/* Assigned Properties */}
      <div className="space-y-2">
        {properties.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Drop properties here to assign them to this team
          </p>
        ) : (
          properties.map((property) => (
            <div key={property.id} className="flex items-center justify-between bg-gray-50 p-2 rounded">
              <div className="flex items-center">
                <Building className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">{property.name}</span>
              </div>
              <button
                onClick={() => onUnassign(property.id)}
                className="text-red-600 hover:text-red-800"
                title="Unassign property"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default PropertyTeamAssignment;
