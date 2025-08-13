import React, { useState, useEffect } from 'react'
import { useAuth } from '../services/auth'
import { api } from '../services/api'
import PropertyList from '../components/PropertyList'
import ReservationsList from '../components/ReservationsList'
import GuestList from '../components/GuestList'
import CommunicationCenter from '../components/CommunicationCenter'
import ContractList from '../components/ContractList'

import TeamsManagement from './TeamsManagement'
import OccupancyCalendar from '../components/OccupancyCalendar'
import PropertyOccupancyChart from '../components/PropertyOccupancyChart'
import { Home, Calendar, Users, Mail, BarChart, FileText, UserCheck, RefreshCw, CheckCircle, UserPlus, Activity } from 'lucide-react'

export default function Dashboard() {
  const { userProfile } = useAuth()
  const [stats, setStats] = useState({
    totalProperties: 0,
    totalReservations: 0,
    upcomingReservations: 0,
    activeGuests: 0,
    occupancy: null
  })
  const [recentActivity, setRecentActivity] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [occupancyPeriod, setOccupancyPeriod] = useState('month')
  const [occupancyData, setOccupancyData] = useState(null)
  const [customDateRange, setCustomDateRange] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [properties, setProperties] = useState([])
  const [reservations, setReservations] = useState([])
  const [showCalendarView, setShowCalendarView] = useState(false)

  useEffect(() => {
    loadDashboardData()
  }, [])

  // Load initial occupancy data
  useEffect(() => {
    if (!loading) {
      loadOccupancyData(occupancyPeriod);
    }
  }, [loading]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const statsResult = await api.getDashboardStats();
      
      if (statsResult.success) {
        setStats(statsResult.stats);
      } else {
        console.error('Failed to load dashboard stats:', statsResult.error);
      }

      // Load properties for interactive components
      const propertiesResult = await api.getProperties();
      if (propertiesResult.success) {
        setProperties(propertiesResult.properties);
      }

      // Load reservations for interactive components
      const allReservationsResult = await api.getReservations({ page: 1, per_page: 100 });
      if (allReservationsResult.success) {
        setReservations(allReservationsResult.reservations);
      }

      // Load recent activity from multiple sources
      const activityResult = await api.getRecentActivity();
      if (activityResult.success) {
        setRecentActivity(activityResult.activities);
      } else {
        console.error('Failed to load recent activity:', activityResult.error);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOccupancyData = async (period, customStartDate = null, customEndDate = null) => {
    try {
      let result;
      if (customDateRange && customStartDate && customEndDate) {
        // Load custom date range data
        result = await api.getOccupancyData(period, customStartDate, customEndDate);
      } else {
        // Load current period data
        result = await api.getOccupancyData(period);
      }
      
      if (result.success) {
        setOccupancyData(result.occupancy);
      } else {
        console.error('Failed to load occupancy data:', result.error);
        // Fallback to basic stats data if API call fails
        if (stats.occupancy) {
          setOccupancyData({
            ...stats.occupancy,
            period: period
          });
        }
      }
    } catch (error) {
      console.error('Error loading occupancy data:', error);
      // Fallback to existing data on error
      if (stats.occupancy) {
        setOccupancyData({
          ...stats.occupancy,
          period: period
        });
      }
    }
  };

  // Load occupancy data when period or custom date range changes
  useEffect(() => {
    if (stats.occupancy) {
      if (customDateRange && startDate && endDate) {
        loadOccupancyData(occupancyPeriod, startDate, endDate);
      } else {
        loadOccupancyData(occupancyPeriod);
      }
    }
  }, [occupancyPeriod, customDateRange, startDate, endDate, stats.occupancy]);

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart },
    { id: 'properties', name: 'Properties', icon: Home },
    { id: 'reservations', name: 'Reservations', icon: Calendar },
    { id: 'guests', name: 'Guests', icon: Users },
    { id: 'communications', name: 'Communications', icon: Mail },
    { id: 'contracts', name: 'Contracts', icon: FileText },
    { id: 'teams', name: 'Teams', icon: UserCheck },
    { id: 'activity', name: 'Activity', icon: Activity }
  ]

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back, {userProfile?.name || 'Host'}!
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage your properties and guest verification from your dashboard
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Property-Centric Mode
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Properties</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalProperties}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 12V11m0 0l-3 3m3-3l3 3" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Reservations</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalReservations}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Upcoming</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.upcomingReservations}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Active Guests</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.activeGuests}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Add Occupancy Stats Card */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart className="h-6 w-6 text-orange-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Average Occupancy</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.occupancy ? `${stats.occupancy.overall}%` : '0%'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Activity</h3>
                  <button 
                    onClick={() => setActiveTab('activity')}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View All →
                  </button>
                </div>
                <div className="mt-4">
                  {recentActivity.length === 0 ? (
                    <p className="text-gray-500 text-sm">No recent activity</p>
                  ) : (
                    <div className="space-y-3">
                      {recentActivity.map((activity, index) => {
                        const getActivityIcon = () => {
                          switch (activity.icon) {
                            case 'calendar':
                              return <Calendar className="h-4 w-4" />;
                            case 'refresh-cw':
                              return <RefreshCw className="h-4 w-4" />;
                            case 'mail':
                              return <Mail className="h-4 w-4" />;
                            case 'file-text':
                              return <FileText className="h-4 w-4" />;
                            case 'user-plus':
                              return <UserPlus className="h-4 w-4" />;
                            case 'check-circle':
                              return <CheckCircle className="h-4 w-4" />;
                            case 'home':
                              return <Home className="h-4 w-4" />;
                            default:
                              return <Activity className="h-4 w-4" />;
                          }
                        };

                        const getActivityColor = () => {
                          switch (activity.color) {
                            case 'blue':
                              return 'bg-blue-100 text-blue-600';
                            case 'green':
                              return 'bg-green-100 text-green-600';
                            case 'purple':
                              return 'bg-purple-100 text-purple-600';
                            case 'orange':
                              return 'bg-orange-100 text-orange-600';
                            case 'indigo':
                              return 'bg-indigo-100 text-indigo-600';
                            default:
                              return 'bg-gray-100 text-gray-600';
                          }
                        };

                        const formatTimestamp = (timestamp) => {
                          const date = new Date(timestamp);
                          const now = new Date();
                          
                          const diffInMs = now.getTime() - date.getTime();
                          const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
                          const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
                          const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
                          
                          // Check if it's today
                          const isToday = now.toDateString() === date.toDateString();
                          // Check if it's yesterday
                          const yesterday = new Date(now);
                          yesterday.setDate(yesterday.getDate() - 1);
                          const isYesterday = yesterday.toDateString() === date.toDateString();
                          
                          if (diffInMinutes < 1) {
                            return 'Just now';
                          } else if (diffInMinutes < 60) {
                            return `${diffInMinutes}m ago`;
                          } else if (isToday) {
                            return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                          } else if (isYesterday) {
                            return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                          } else if (diffInDays < 7) {
                            const dayName = date.toLocaleDateString([], { weekday: 'short' });
                            return `${dayName} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                          } else {
                            return date.toLocaleDateString([], { 
                              month: 'short', 
                              day: 'numeric',
                              ...(date.getFullYear() !== now.getFullYear() ? { year: 'numeric' } : {})
                            });
                          }
                        };

                        return (
                          <div key={activity.id || index} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                            <div className="flex-shrink-0">
                              <div className={`h-8 w-8 rounded-full flex items-center justify-center ${getActivityColor()}`}>
                                {getActivityIcon()}
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                              <p className="text-xs text-gray-500">{activity.description}</p>
                              <p className="text-xs text-gray-400">{activity.property_name}</p>
                            </div>
                            <div className="flex-shrink-0 text-xs text-gray-500">
                              {formatTimestamp(activity.timestamp)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Occupancy Analysis */}
              {occupancyData && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                      <BarChart className="h-5 w-5 mr-2 text-blue-600" />
                      Occupancy Analysis
                    </h3>
                                         <div className="flex items-center space-x-4">
                       <div className="flex items-center space-x-2">
                         <label className="text-sm text-gray-600">Period:</label>
                         <select
                           value={occupancyPeriod}
                           onChange={(e) => setOccupancyPeriod(e.target.value)}
                           className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                         >
                           <option value="week">This Week</option>
                           <option value="month">This Month</option>
                           <option value="quarter">This Quarter</option>
                           <option value="year">This Year</option>
                         </select>
                       </div>
                       
                       <div className="flex items-center space-x-2">
                         <label className="text-sm text-gray-600">Date Range:</label>
                         <div className="flex items-center space-x-2">
                           <button
                             onClick={() => setCustomDateRange(false)}
                             className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                               !customDateRange
                                 ? 'bg-blue-100 text-blue-700'
                                 : 'text-gray-600 hover:text-gray-900'
                             }`}
                           >
                             Current
                           </button>
                           <button
                             onClick={() => setCustomDateRange(true)}
                             className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                               customDateRange
                                 ? 'bg-blue-100 text-blue-700'
                                 : 'text-gray-600 hover:text-gray-900'
                             }`}
                           >
                             Custom
                           </button>
                         </div>
                       </div>
                       
                       {customDateRange && (
                         <div className="flex items-center space-x-2">
                           <input
                             type="date"
                             value={startDate}
                             onChange={(e) => setStartDate(e.target.value)}
                             className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                             placeholder="Start Date"
                           />
                           <span className="text-gray-500">to</span>
                           <input
                             type="date"
                             value={endDate}
                             onChange={(e) => setEndDate(e.target.value)}
                             className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                             placeholder="End Date"
                           />
                           
                           {/* Quick preset buttons */}
                           <div className="flex items-center space-x-1 ml-2">
                             <button
                               onClick={() => {
                                 const today = new Date();
                                 const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                                 const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                                 setStartDate(lastMonth.toISOString().split('T')[0]);
                                 setEndDate(lastMonthEnd.toISOString().split('T')[0]);
                               }}
                               className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                             >
                               Last Month
                             </button>
                             <button
                               onClick={() => {
                                 const today = new Date();
                                 const lastQuarter = new Date(today.getFullYear(), Math.floor((today.getMonth() - 3) / 3) * 3, 1);
                                 const lastQuarterEnd = new Date(today.getFullYear(), Math.floor((today.getMonth() - 3) / 3) * 3 + 3, 0);
                                 setStartDate(lastQuarter.toISOString().split('T')[0]);
                                 setEndDate(lastQuarterEnd.toISOString().split('T')[0]);
                               }}
                               className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                             >
                               Last Quarter
                             </button>
                             <button
                               onClick={() => {
                                 const today = new Date();
                                 const lastYear = new Date(today.getFullYear() - 1, 0, 1);
                                 const lastYearEnd = new Date(today.getFullYear() - 1, 11, 31);
                                 setStartDate(lastYear.toISOString().split('T')[0]);
                                 setEndDate(lastYearEnd.toISOString().split('T')[0]);
                               }}
                               className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                             >
                               Last Year
                             </button>
                           </div>
                         </div>
                       )}
                       
                       <div className="flex items-center space-x-2">
                         <label className="text-sm text-gray-600">View:</label>
                         <div className="bg-gray-100 p-1 rounded-lg flex">
                           <button
                             onClick={() => setShowCalendarView(false)}
                             className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                               !showCalendarView
                                 ? 'bg-white text-gray-900 shadow-sm'
                                 : 'text-gray-600 hover:text-gray-900'
                             }`}
                           >
                             <BarChart className="h-4 w-4 mr-1 inline" />
                             Charts
                           </button>
                           <button
                             onClick={() => setShowCalendarView(true)}
                             className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                               showCalendarView
                                 ? 'bg-white text-gray-900 shadow-sm'
                                 : 'text-gray-600 hover:text-gray-900'
                             }`}
                           >
                             <Calendar className="h-4 w-4 mr-1 inline" />
                             Calendar
                           </button>
                         </div>
                       </div>
                     </div>
                  </div>

                                     {/* Interactive Occupancy Views */}
                   <div className="space-y-6">
                     {showCalendarView ? (
                       /* Calendar View */
                       <OccupancyCalendar 
                         occupancyData={occupancyData}
                         properties={properties}
                         reservations={reservations}
                       />
                     ) : (
                       /* Charts View */
                       <div className="space-y-6">
                         {/* Summary Cards */}
                         <div className={`grid gap-6 ${occupancyData.isCustomRange ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 lg:grid-cols-3'}`}>
                           {/* Overall Occupancy */}
                           <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                             <div className="flex items-center justify-between">
                               <div>
                                 <h4 className="text-lg font-medium">Overall Occupancy</h4>
                                 <p className="text-blue-100 text-sm">
                                   {occupancyData.isCustomRange ? 'Custom Range' :
                                    occupancyPeriod === 'week' ? 'Weekly' : 
                                    occupancyPeriod === 'month' ? 'Monthly' : 
                                    occupancyPeriod === 'quarter' ? 'Quarterly' : 'Yearly'} average
                                 </p>
                               </div>
                               <div className="text-3xl font-bold">{occupancyData.overall}%</div>
                             </div>
                           </div>

                           {/* Current Period */}
                           <div className="bg-white border-2 border-gray-200 rounded-lg p-6">
                             <div className="flex items-center justify-between mb-4">
                               <h4 className="text-lg font-medium text-gray-900">
                                 {occupancyData.currentPeriod?.label || occupancyData.currentMonth?.month || 'Current Period'}
                               </h4>
                               <div className="text-2xl font-bold text-green-600">
                                 {occupancyData.currentPeriod?.rate || occupancyData.currentMonth?.rate || 0}%
                               </div>
                             </div>
                             <div className="space-y-2">
                               <div className="flex justify-between text-sm">
                                 <span className="text-gray-600">Booked Nights:</span>
                                 <span className="font-medium">
                                   {occupancyData.currentPeriod?.bookedNights || occupancyData.currentMonth?.bookedNights || 0}
                                 </span>
                               </div>
                               <div className="flex justify-between text-sm">
                                 <span className="text-gray-600">Total Available:</span>
                                 <span className="font-medium">
                                   {occupancyData.currentPeriod?.totalNights || occupancyData.currentMonth?.totalNights || 0}
                                 </span>
                               </div>
                               <div className="w-full bg-gray-200 rounded-full h-2">
                                 <div 
                                   className="bg-green-600 h-2 rounded-full" 
                                   style={{ width: `${occupancyData.currentPeriod?.rate || occupancyData.currentMonth?.rate || 0}%` }}
                                 ></div>
                               </div>
                             </div>
                           </div>

                           {/* Future Period - Only show for non-custom ranges */}
                           {!occupancyData.isCustomRange && (
                             <div className="bg-white border-2 border-gray-200 rounded-lg p-6">
                               <div className="flex items-center justify-between mb-4">
                                 <h4 className="text-lg font-medium text-gray-900">
                                   {occupancyData.futurePeriod?.label || occupancyData.nextMonth?.month || 'Next Period'}
                                 </h4>
                                 <div className="text-2xl font-bold text-blue-600">
                                   {occupancyData.futurePeriod?.rate || occupancyData.nextMonth?.rate || 0}%
                                 </div>
                               </div>
                               <div className="space-y-2">
                                 <div className="flex justify-between text-sm">
                                   <span className="text-gray-600">Booked Nights:</span>
                                   <span className="font-medium">
                                     {occupancyData.futurePeriod?.bookedNights || occupancyData.nextMonth?.bookedNights || 0}
                                   </span>
                                 </div>
                                 <div className="flex justify-between text-sm">
                                   <span className="text-gray-600">Total Available:</span>
                                   <span className="font-medium">
                                     {occupancyData.futurePeriod?.totalNights || occupancyData.nextMonth?.totalNights || 0}
                                   </span>
                                 </div>
                                 <div className="w-full bg-gray-200 rounded-full h-2">
                                   <div 
                                     className="bg-blue-600 h-2 rounded-full" 
                                     style={{ width: `${occupancyData.futurePeriod?.rate || occupancyData.nextMonth?.rate || 0}%` }}
                                   ></div>
                                 </div>
                               </div>
                             </div>
                           )}
                         </div>

                         {/* Property Performance Chart */}
                         <PropertyOccupancyChart 
                           occupancyData={occupancyData}
                           period={occupancyPeriod}
                         />
                       </div>
                     )}
                   </div>
                </div>
              )}

              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">Quick Actions</h3>
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    onClick={() => setActiveTab('properties')}
                    className="relative bg-white p-6 border border-gray-300 rounded-lg hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <div>
                      <span className="rounded-lg inline-flex p-3 bg-blue-50 text-blue-700">
                        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      </span>
                    </div>
                    <div className="mt-4">
                      <h3 className="text-lg font-medium text-gray-900">Manage Properties</h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Add properties and configure calendar sync
                      </p>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('reservations')}
                    className="relative bg-white p-6 border border-gray-300 rounded-lg hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <div>
                      <span className="rounded-lg inline-flex p-3 bg-green-50 text-green-700">
                        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 12V11m0 0l-3 3m3-3l3 3" />
                        </svg>
                      </span>
                    </div>
                    <div className="mt-4">
                      <h3 className="text-lg font-medium text-gray-900">View Reservations</h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Check upcoming and current reservations
                      </p>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('guests')}
                    className="relative bg-white p-6 border border-gray-300 rounded-lg hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <div>
                      <span className="rounded-lg inline-flex p-3 bg-purple-50 text-purple-700">
                        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </span>
                    </div>
                    <div className="mt-4">
                      <h3 className="text-lg font-medium text-gray-900">Guest Verification</h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Manage guest verification and contracts
                      </p>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'properties' && (
            <PropertyList onSyncComplete={loadDashboardData} />
          )}

          {activeTab === 'reservations' && (
            <ReservationsList />
          )}

          {activeTab === 'guests' && (
            <GuestList />
          )}

          {activeTab === 'communications' && (
            <CommunicationCenter />
          )}

          {activeTab === 'contracts' && (
            <ContractList />
          )}

          {activeTab === 'teams' && (
            <TeamsManagement />
          )}

          {activeTab === 'activity' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">All Activities</h3>
                <div className="bg-white shadow rounded-lg">
                  <div className="p-6">
                    {recentActivity.length === 0 ? (
                      <p className="text-gray-500 text-sm">No activities found</p>
                    ) : (
                      <div className="space-y-4">
                        {recentActivity.map((activity, index) => {
                          const getActivityIcon = () => {
                            switch (activity.icon) {
                              case 'calendar':
                                return <Calendar className="h-4 w-4" />;
                              case 'refresh-cw':
                                return <RefreshCw className="h-4 w-4" />;
                              case 'mail':
                                return <Mail className="h-4 w-4" />;
                              case 'file-text':
                                return <FileText className="h-4 w-4" />;
                              case 'user-plus':
                                return <UserPlus className="h-4 w-4" />;
                              case 'check-circle':
                                return <CheckCircle className="h-4 w-4" />;
                              case 'home':
                                return <Home className="h-4 w-4" />;
                              default:
                                return <Activity className="h-4 w-4" />;
                            }
                          };

                          const getActivityColor = () => {
                            switch (activity.color) {
                              case 'blue':
                                return 'bg-blue-100 text-blue-600';
                              case 'green':
                                return 'bg-green-100 text-green-600';
                              case 'purple':
                                return 'bg-purple-100 text-purple-600';
                              case 'orange':
                                return 'bg-orange-100 text-orange-600';
                              case 'indigo':
                                return 'bg-indigo-100 text-indigo-600';
                              default:
                                return 'bg-gray-100 text-gray-600';
                            }
                          };

                          const formatTimestamp = (timestamp) => {
                            const date = new Date(timestamp);
                            const now = new Date();
                            
                            const diffInMs = now.getTime() - date.getTime();
                            const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
                            const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
                            const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
                            
                            // Check if it's today
                            const isToday = now.toDateString() === date.toDateString();
                            // Check if it's yesterday
                            const yesterday = new Date(now);
                            yesterday.setDate(yesterday.getDate() - 1);
                            const isYesterday = yesterday.toDateString() === date.toDateString();
                            
                            if (diffInMinutes < 1) {
                              return 'Just now';
                            } else if (diffInMinutes < 60) {
                              return `${diffInMinutes}m ago`;
                            } else if (isToday) {
                              return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                            } else if (isYesterday) {
                              return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                            } else if (diffInDays < 7) {
                              const dayName = date.toLocaleDateString([], { weekday: 'short' });
                              return `${dayName} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                            } else {
                              return date.toLocaleDateString([], { 
                                month: 'short', 
                                day: 'numeric',
                                ...(date.getFullYear() !== now.getFullYear() ? { year: 'numeric' } : {})
                              });
                            }
                          };

                          return (
                            <div key={activity.id || index} className="flex items-center space-x-4 p-4 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                              <div className="flex-shrink-0">
                                <div className={`h-10 w-10 rounded-full flex items-center justify-center ${getActivityColor()}`}>
                                  {getActivityIcon()}
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                                <p className="text-xs text-gray-500">{activity.description}</p>
                                <p className="text-xs text-gray-400">{activity.property_name}</p>
                              </div>
                              <div className="flex-shrink-0 text-xs text-gray-500">
                                {formatTimestamp(activity.timestamp)}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}


        </div>
      </div>
    </div>
  )
} 