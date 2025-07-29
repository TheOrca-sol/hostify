import React, { useState } from 'react'
import { BarChart3, TrendingUp, TrendingDown, Home, Eye, EyeOff } from 'lucide-react'

const PropertyOccupancyChart = ({ occupancyData, period = 'month' }) => {
  const [sortBy, setSortBy] = useState('rate') // 'rate', 'name', 'bookedDays'
  const [sortOrder, setSortOrder] = useState('desc') // 'asc', 'desc'
  const [showDetails, setShowDetails] = useState(true)

  if (!occupancyData || !occupancyData.properties) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>No property data available</p>
        </div>
      </div>
    )
  }

  // Sort properties
  const sortedProperties = [...occupancyData.properties].sort((a, b) => {
    let comparison = 0
    
    switch (sortBy) {
      case 'rate':
        comparison = a.rate - b.rate
        break
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'bookedDays':
        comparison = a.bookedDays - b.bookedDays
        break
      default:
        comparison = a.rate - b.rate
    }
    
    return sortOrder === 'desc' ? -comparison : comparison
  })

  const maxRate = Math.max(...occupancyData.properties.map(p => p.rate), 100)
  const maxBookedDays = Math.max(...occupancyData.properties.map(p => p.bookedDays))

  const getPerformanceIcon = (rate) => {
    if (rate >= 80) return <TrendingUp className="h-4 w-4 text-green-600" />
    if (rate >= 60) return <TrendingUp className="h-4 w-4 text-blue-600" />
    if (rate >= 40) return <TrendingDown className="h-4 w-4 text-yellow-600" />
    return <TrendingDown className="h-4 w-4 text-red-600" />
  }

  const getPerformanceColor = (rate) => {
    if (rate >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (rate >= 60) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (rate >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getBarColor = (rate) => {
    if (rate >= 80) return 'bg-green-500'
    if (rate >= 60) return 'bg-blue-500'
    if (rate >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const handleSort = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(newSortBy)
      setSortOrder('desc')
    }
  }

  const getSortIcon = (field) => {
    if (sortBy !== field) return null
    return (
      <span className="ml-1">
        {sortOrder === 'asc' ? '↑' : '↓'}
      </span>
    )
  }

  const averageRate = occupancyData.properties.reduce((sum, p) => sum + p.rate, 0) / occupancyData.properties.length

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
            Property Performance Breakdown
          </h3>
                     <span className="text-sm text-gray-500">
             ({occupancyData.currentPeriod?.label || occupancyData.currentMonth?.month || period})
           </span>
        </div>

        <div className="flex items-center space-x-4">
          {/* Sort Controls */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Sort by:</span>
            <button
              onClick={() => handleSort('rate')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                sortBy === 'rate' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Rate {getSortIcon('rate')}
            </button>
            <button
              onClick={() => handleSort('bookedDays')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                sortBy === 'bookedDays' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Days {getSortIcon('bookedDays')}
            </button>
            <button
              onClick={() => handleSort('name')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                sortBy === 'name' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Name {getSortIcon('name')}
            </button>
          </div>

          {/* Toggle Details */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            title={showDetails ? 'Hide details' : 'Show details'}
          >
            {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">{occupancyData.properties.length}</div>
          <div className="text-sm text-blue-700">Total Properties</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">{averageRate.toFixed(1)}%</div>
          <div className="text-sm text-green-700">Average Rate</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {occupancyData.properties.filter(p => p.rate >= 80).length}
          </div>
          <div className="text-sm text-purple-700">High Performers</div>
        </div>
        <div className="bg-orange-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {occupancyData.properties.filter(p => p.rate < 40).length}
          </div>
          <div className="text-sm text-orange-700">Need Attention</div>
        </div>
      </div>

      {/* Property Charts */}
      <div className="space-y-4">
        {sortedProperties.map((property, index) => (
          <div key={property.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <Home className="h-4 w-4 text-gray-500" />
                  <h4 className="font-medium text-gray-900">{property.name}</h4>
                </div>
                {getPerformanceIcon(property.rate)}
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">{property.rate}%</div>
                  <div className="text-sm text-gray-600">Occupancy</div>
                </div>
                <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getPerformanceColor(property.rate)}`}>
                  {property.rate >= 80 ? 'Excellent' : 
                   property.rate >= 60 ? 'Good' : 
                   property.rate >= 40 ? 'Fair' : 'Poor'}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Occupancy Rate</span>
                <span>{property.bookedDays}/{property.totalDays} days</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 relative overflow-hidden">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${getBarColor(property.rate)}`}
                  style={{ width: `${(property.rate / maxRate) * 100}%` }}
                ></div>
                {/* Average line */}
                <div 
                  className="absolute top-0 w-0.5 h-3 bg-gray-800 opacity-50"
                  style={{ left: `${(averageRate / maxRate) * 100}%` }}
                  title={`Average: ${averageRate.toFixed(1)}%`}
                ></div>
              </div>
            </div>

            {/* Detailed Stats */}
            {showDetails && (
              <div className="grid grid-cols-3 gap-4 pt-3 border-t border-gray-100">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">{property.bookedDays}</div>
                  <div className="text-sm text-gray-600">Booked Days</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">{property.totalDays - property.bookedDays}</div>
                  <div className="text-sm text-gray-600">Available Days</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {property.rate > averageRate ? '+' : ''}{(property.rate - averageRate).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600">vs Average</div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Bottom Legend */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-center space-x-6 text-sm text-gray-600">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-800 opacity-50"></div>
            <span>Average Line</span>
          </div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span>High Performance (60%+)</span>
          </div>
          <div className="flex items-center space-x-2">
            <TrendingDown className="h-4 w-4 text-red-600" />
            <span>Needs Attention (&lt;40%)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PropertyOccupancyChart 