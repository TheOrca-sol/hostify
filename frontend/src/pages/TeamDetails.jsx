import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { Building, Users, BarChart3, ArrowLeft } from 'lucide-react';
import TeamPerformanceDashboard from '../components/TeamPerformanceDashboard';
import PropertyTeamAssignment from '../components/PropertyTeamAssignment';

const TeamDetails = () => {
    const { teamId } = useParams();
    const [team, setTeam] = useState(null);
    const [members, setMembers] = useState([]);
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('dashboard');

    useEffect(() => {
        loadTeamDetails();
    }, [teamId]);

    const loadTeamDetails = async () => {
        try {
            setLoading(true);
            // This is a placeholder; you'll need a `getTeam` endpoint
            const teamsResponse = await api.getTeams();
            if (teamsResponse.success) {
                const currentTeam = teamsResponse.owned_teams.find(t => t.id === teamId) || teamsResponse.member_teams.find(t => t.id === teamId);
                setTeam(currentTeam);
            }

            const membersResponse = await api.getTeamMembers(teamId);
            if (membersResponse.success) {
                setMembers(membersResponse.members || []);
            }

            const propertiesResponse = await api.getTeamProperties(teamId);
            if (propertiesResponse.success) {
                setProperties(propertiesResponse.properties || []);
            }
        } catch (error) {
            toast.error('Failed to load team details');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="text-center p-8">Loading team details...</div>;
    }

    if (!team) {
        return <div className="text-center p-8">Team not found.</div>;
    }

    const tabs = [
        { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
        { id: 'members', name: 'Members', icon: Users },
        { id: 'properties', name: 'Properties', icon: Building },
    ];

    return (
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
            <Link to="/" className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4">
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Dashboard
            </Link>
            
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
                <div style={{ backgroundColor: team.color }} className="w-8 h-8 rounded-full"></div>
            </div>

            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`${
                                activeTab === tab.id
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                        >
                            <tab.icon className="h-5 w-5 mr-2" />
                            {tab.name}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="mt-8">
                {activeTab === 'dashboard' && <TeamPerformanceDashboard teamId={teamId} teamName={team.name} />}
                {activeTab === 'members' && <TeamMembersList members={members} />}
                {activeTab === 'properties' && <TeamPropertiesList properties={properties} />}
            </div>
        </div>
    );
};

const TeamMembersList = ({ members }) => (
    <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Team Members ({members.length})</h2>
        <ul className="divide-y divide-gray-200">
            {members.map(member => (
                <li key={member.user_id} className="py-4 flex justify-between items-center">
                    <div>
                        <p className="text-md font-medium text-gray-900">{member.user_name}</p>
                        <p className="text-sm text-gray-500">{member.user_email}</p>
                    </div>
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {member.role}
                    </span>
                </li>
            ))}
        </ul>
    </div>
);

const TeamPropertiesList = ({ properties }) => (
    <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Assigned Properties ({properties.length})</h2>
        <ul className="divide-y divide-gray-200">
            {properties.map(prop => (
                <li key={prop.id} className="py-4">
                    <p className="text-md font-medium text-gray-900">{prop.name}</p>
                    <p className="text-sm text-gray-500">{prop.address}</p>
                </li>
            ))}
        </ul>
        <div className="mt-6">
            <h3 className="text-lg font-semibold mb-4">Assign More Properties</h3>
            <PropertyTeamAssignment />
        </div>
    </div>
);

export default TeamDetails;
