import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import {
  BarChart3,
  Clock,
  DollarSign,
  Trophy,
  ArrowUp,
  ArrowDown,
  Calendar,
  Users
} from 'lucide-react';

const TeamPerformanceDashboard = ({ teamId, teamName }) => {
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('30');
  const [comparisonData, setComparisonData] = useState(null);

  useEffect(() => {
    loadPerformanceData();
  }, [teamId, dateRange]);

  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - parseInt(dateRange));
      
      const [performanceResponse, comparisonResponse] = await Promise.all([
        api.getTeamPerformance(
          teamId, 
          startDate.toISOString().split('T')[0], 
          endDate.toISOString().split('T')[0]
        ),
        api.getOrganizationPerformanceComparison()
      ]);
      
      if (performanceResponse.success) {
        setPerformanceData(performanceResponse);
      }
      
      if (comparisonResponse.success) {
        setComparisonData(comparisonResponse);
      }
    } catch (error) {
      console.error('Error loading performance data:', error);
      toast.error('Failed to load performance data');
    } finally {
      setLoading(false);
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
      case 'decimal':
        return Math.round(value * 10) / 10;
      default:
        return Math.round(value).toLocaleString();
    }
  };

  const getChangeIndicator = (current, previous) => {
    if (!current || !previous) return null;
    
    const change = ((current - previous) / previous) * 100;
    const isPositive = change > 0;
    
    return (
      <span className={`inline-flex items-center text-sm ${
        isPositive ? 'text-green-600' : 'text-red-600'
      }`}>
        {isPositive ? (
          <ArrowUp className="h-4 w-4 mr-1" />
        ) : (
          <ArrowDown className="h-4 w-4 mr-1" />
        )}
        {Math.abs(change).toFixed(1)}%
      </span>
    );
  };

  const getTeamRanking = () => {
    if (!comparisonData || !performanceData) return null;
    
    const teams = comparisonData.teams || [];
    const currentTeam = teams.find(t => t.id === teamId);
    
    if (!currentTeam) return null;
    
    // Sort teams by efficiency score
    const sortedTeams = teams.sort((a, b) => 
      (b.performance?.efficiency_score || 0) - (a.performance?.efficiency_score || 0)
    );
    
    const rank = sortedTeams.findIndex(t => t.id === teamId) + 1;
    
    return {
      rank,
      total: teams.length,
      score: currentTeam.performance?.efficiency_score || 0
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!performanceData) {
    return (
      <div className="text-center py-8">
        <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No performance data</h3>
        <p className="mt-1 text-sm text-gray-500">Data will appear as your team completes tasks.</p>
      </div>
    );
  }

  const metrics = performanceData.metrics || {};
  const ranking = getTeamRanking();

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          {teamName} Performance
        </h2>
        <div className="flex items-center space-x-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Team Ranking */}
      {ranking && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <Trophy className="h-8 w-8 text-yellow-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-900">Team Ranking</p>
              <p className="text-lg font-bold text-yellow-700">
                #{ranking.rank} of {ranking.total} teams
              </p>
              <p className="text-sm text-gray-600">
                Efficiency Score: {formatMetric(ranking.score, 'percentage')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Task Completion"
          value={formatMetric(metrics.task_completion_rate, 'percentage')}
          icon={BarChart3}
          color="blue"
          change={getChangeIndicator(metrics.task_completion_rate, 85)} // Mock previous value
        />
        <MetricCard
          title="Response Time"
          value={formatMetric(metrics.average_response_time, 'time')}
          icon={Clock}
          color="green"
          change={getChangeIndicator(45, metrics.average_response_time)} // Lower is better
        />
        <MetricCard
          title="Guest Satisfaction"
          value={formatMetric(metrics.guest_satisfaction, 'percentage')}
          icon={Users}
          color="purple"
          change={getChangeIndicator(metrics.guest_satisfaction, 88)}
        />
        <MetricCard
          title="Revenue Generated"
          value={formatMetric(metrics.revenue, 'currency')}
          icon={DollarSign}
          color="green"
          change={getChangeIndicator(metrics.revenue, 12500)}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Property & Booking Stats */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Property & Bookings</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Properties Managed</span>
              <span className="text-sm font-medium text-gray-900">
                {formatMetric(metrics.properties_managed, 'number')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Bookings</span>
              <span className="text-sm font-medium text-gray-900">
                {formatMetric(metrics.total_bookings, 'number')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Efficiency Score</span>
              <span className="text-sm font-medium text-gray-900">
                {formatMetric(metrics.efficiency_score, 'percentage')}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Trends */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Trends</h3>
          <div className="space-y-4">
            {performanceData.daily_records && performanceData.daily_records.slice(0, 5).map((record, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">
                  {new Date(record.date).toLocaleDateString()}
                </span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">
                    {formatMetric(record.metrics?.efficiency_score, 'percentage')}
                  </span>
                  <div className={`w-3 h-3 rounded-full ${
                    record.metrics?.efficiency_score > 80 ? 'bg-green-400' :
                    record.metrics?.efficiency_score > 60 ? 'bg-yellow-400' : 'bg-red-400'
                  }`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team Comparison Chart */}
      {comparisonData && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Team Comparison</h3>
          <div className="space-y-3">
            {comparisonData.teams.map((team) => (
              <div key={team.id} className="flex items-center">
                <div className="w-24 text-sm text-gray-600 truncate" title={team.name}>
                  {team.name}
                </div>
                <div className="flex-1 mx-4">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        team.id === teamId ? 'bg-blue-600' : 'bg-gray-400'
                      }`}
                      style={{
                        width: `${Math.min((team.performance?.efficiency_score || 0), 100)}%`
                      }}
                    ></div>
                  </div>
                </div>
                <div className="w-12 text-sm text-gray-900 text-right">
                  {formatMetric(team.performance?.efficiency_score, 'percentage')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color, change }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600'
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <div className="flex items-center">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {change && <div className="ml-2">{change}</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamPerformanceDashboard;
