import React, { useState, useMemo } from 'react'
import { Calendar, ChevronLeft, ChevronRight, Home, Users } from 'lucide-react'

const OccupancyCalendar = ({ occupancyData, properties, reservations }) => {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedProperty, setSelectedProperty] = useState('all')

  // Generate calendar days for current month
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days = []
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }

    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day)
      const dateStr = date.toISOString().split('T')[0]
      
             // Calculate occupancy for this day using proper overlap handling
       let totalProperties = properties ? properties.length : 1
       let occupiedPropertyIds = new Set() // Track unique properties to avoid double-counting overlaps
       
       if (selectedProperty === 'all') {
         // Check all properties
         if (reservations) {
           reservations.forEach(reservation => {
             const checkIn = new Date(reservation.check_in)
             const checkOut = new Date(reservation.check_out)
             // Check if this date falls within the reservation (exclusive end date)
             if (date >= checkIn && date < checkOut) {
               occupiedPropertyIds.add(reservation.property_id)
             }
           })
         }
       } else {
         // Check specific property
         totalProperties = 1
         if (reservations) {
           const propertyReservations = reservations.filter(r => r.property_id === selectedProperty)
           propertyReservations.forEach(reservation => {
             const checkIn = new Date(reservation.check_in)
             const checkOut = new Date(reservation.check_out)
             // Check if this date falls within the reservation (exclusive end date)
             if (date >= checkIn && date < checkOut) {
               occupiedPropertyIds.add(selectedProperty)
             }
           })
         }
       }

       const occupiedProperties = occupiedPropertyIds.size
       const occupancyRate = totalProperties > 0 ? (occupiedProperties / totalProperties) * 100 : 0
      
      days.push({
        day,
        date,
        dateStr,
        occupancyRate,
        occupiedProperties,
        totalProperties
      })
    }

    return days
  }, [currentDate, selectedProperty, properties, reservations])

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  const navigateMonth = (direction) => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      newDate.setMonth(prev.getMonth() + direction)
      return newDate
    })
  }

  const getOccupancyColor = (rate) => {
    if (rate === 0) return 'bg-gray-100 border-gray-200'
    if (rate <= 25) return 'bg-red-100 border-red-200'
    if (rate <= 50) return 'bg-yellow-100 border-yellow-200'
    if (rate <= 75) return 'bg-blue-100 border-blue-200'
    return 'bg-green-100 border-green-200'
  }

  const getOccupancyTextColor = (rate) => {
    if (rate === 0) return 'text-gray-600'
    if (rate <= 25) return 'text-red-600'
    if (rate <= 50) return 'text-yellow-600'
    if (rate <= 75) return 'text-blue-600'
    return 'text-green-600'
  }

  const today = new Date()
  const isToday = (date) => {
    return date && 
           date.getDate() === today.getDate() && 
           date.getMonth() === today.getMonth() && 
           date.getFullYear() === today.getFullYear()
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Calendar className="h-5 w-5 mr-2 text-blue-600" />
            Occupancy Calendar
          </h3>
          
          {/* Property Filter */}
          <select
            value={selectedProperty}
            onChange={(e) => setSelectedProperty(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Properties</option>
            {properties && properties.map(property => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
        </div>

        {/* Month Navigation */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigateMonth(-1)}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          
          <h4 className="text-lg font-medium min-w-[180px] text-center">
            {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
          </h4>
          
          <button
            onClick={() => navigateMonth(1)}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mb-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-100 border border-gray-200 rounded"></div>
          <span className="text-gray-600">0% (Empty)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-100 border border-red-200 rounded"></div>
          <span className="text-gray-600">1-25%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-yellow-100 border border-yellow-200 rounded"></div>
          <span className="text-gray-600">26-50%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
          <span className="text-gray-600">51-75%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-100 border border-green-200 rounded"></div>
          <span className="text-gray-600">76-100%</span>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Day Headers */}
        {dayNames.map(dayName => (
          <div key={dayName} className="p-2 text-center text-sm font-medium text-gray-500">
            {dayName}
          </div>
        ))}

        {/* Calendar Days */}
        {calendarDays.map((day, index) => (
          <div key={index} className="aspect-square">
            {day ? (
              <div 
                className={`
                  w-full h-full p-1 border rounded cursor-pointer transition-all hover:shadow-md
                  ${getOccupancyColor(day.occupancyRate)}
                  ${isToday(day.date) ? 'ring-2 ring-blue-500' : ''}
                `}
                title={`${day.dateStr}: ${day.occupancyRate.toFixed(1)}% occupied (${day.occupiedProperties}/${day.totalProperties})`}
              >
                <div className="w-full h-full flex flex-col items-center justify-center">
                  <div className={`text-sm font-medium ${getOccupancyTextColor(day.occupancyRate)}`}>
                    {day.day}
                  </div>
                  {day.occupancyRate > 0 && (
                    <div className={`text-xs ${getOccupancyTextColor(day.occupancyRate)}`}>
                      {day.occupancyRate.toFixed(0)}%
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="w-full h-full"></div>
            )}
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-lg font-bold text-gray-900">
            {calendarDays.filter(day => day && day.occupancyRate > 0).length}
          </div>
                          <div className="text-sm text-gray-600">Occupied Nights</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-lg font-bold text-gray-900">
            {calendarDays.filter(day => day && day.occupancyRate === 100).length}
          </div>
          <div className="text-sm text-gray-600">Fully Booked</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-lg font-bold text-gray-900">
            {calendarDays.filter(day => day && day.occupancyRate === 0).length}
          </div>
                          <div className="text-sm text-gray-600">Available Nights</div>
        </div>
      </div>
    </div>
  )
}

export default OccupancyCalendar