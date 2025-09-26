# 🔐 Smart Lock Frontend Integration Guide

## 📦 Components Created

We've built a comprehensive set of React components for smart lock integration:

### 🏠 **Property Management**
- **`PropertySmartLockSettings.jsx`** - Configure smart lock type per property
- **`SmartLockVariableSelector.jsx`** - Helper for template variables

### 🎫 **Reservation Management**
- **`ReservationPasscodeManager.jsx`** - Manage passcodes for individual reservations
- **`ReservationDetails.jsx`** - Complete reservation details page with smart lock integration
- **`PendingPasscodes.jsx`** - Dashboard widget for manual passcode entries

### 📧 **Message Templates**
- **`EnhancedMessageTemplateEditor.jsx`** - Template editor with smart lock variables

### 🔌 **API Integration**
- Updated `api.js` with 15+ new smart lock endpoints

---

## 🚀 Integration Steps

### 1. **Dashboard Integration**

Add the PendingPasscodes widget to your main dashboard:

```jsx
// In your Dashboard.jsx
import PendingPasscodes from '../components/PendingPasscodes'

function Dashboard() {
  return (
    <div className="dashboard-grid">
      {/* Your existing widgets */}

      {/* Add this widget */}
      <PendingPasscodes />

      {/* Other widgets */}
    </div>
  )
}
```

### 2. **Property Settings Integration**

Add smart lock settings to your property management:

```jsx
// In your PropertyDetails.jsx or PropertySettings.jsx
import PropertySmartLockSettings from '../components/PropertySmartLockSettings'

function PropertyDetails({ propertyId }) {
  return (
    <div className="property-details">
      {/* Your existing property sections */}

      {/* Add smart lock configuration */}
      <PropertySmartLockSettings
        propertyId={propertyId}
        onSettingsUpdate={(settings) => {
          // Optional: Handle settings updates
          console.log('Smart lock settings updated:', settings)
        }}
      />
    </div>
  )
}
```

### 3. **Reservation Details Integration**

Option A: **Use the complete ReservationDetails page**
```jsx
// Add to your router (App.jsx or router config)
import ReservationDetails from './pages/ReservationDetails'

// Add this route
<Route path="/reservations/:id" element={<ReservationDetails />} />
```

Option B: **Add component to existing reservation page**
```jsx
// In your existing reservation page
import ReservationPasscodeManager from '../components/ReservationPasscodeManager'

function YourReservationPage({ reservation }) {
  return (
    <div>
      {/* Your existing reservation content */}

      {/* Add smart lock passcode management */}
      <ReservationPasscodeManager reservation={reservation} />
    </div>
  )
}
```

### 4. **Message Templates Integration**

Replace your existing template editor with the enhanced version:

```jsx
// In your message template page
import EnhancedMessageTemplateEditor from '../components/EnhancedMessageTemplateEditor'

function MessageTemplates() {
  const [reservations, setReservations] = useState([])

  // Load reservations for testing
  useEffect(() => {
    api.getReservations().then(result => {
      if (result.success) setReservations(result.reservations)
    })
  }, [])

  return (
    <EnhancedMessageTemplateEditor
      template={selectedTemplate}
      onSave={handleSaveTemplate}
      reservations={reservations}
      properties={properties}
    />
  )
}
```

### 5. **Reservations Table Enhancement**

Add passcode status column to your reservations table:

```jsx
// In ReservationsList.jsx or similar
function ReservationRow({ reservation }) {
  const [passcode, setPasscode] = useState(null)

  useEffect(() => {
    // Load passcode data
    api.getReservationPasscode(reservation.id).then(result => {
      if (result.success) setPasscode(result.passcode_data)
    })
  }, [reservation.id])

  return (
    <tr>
      {/* Your existing columns */}

      {/* Add passcode status column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        {passcode ? (
          <div className="flex items-center">
            <Lock className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-700">
              {passcode.passcode || 'Pending'}
            </span>
          </div>
        ) : (
          <span className="text-gray-500">No passcode</span>
        )}
      </td>

      {/* Action column */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <Link
          to={`/reservations/${reservation.id}`}
          className="text-blue-600 hover:text-blue-900"
        >
          View Details
        </Link>
      </td>
    </tr>
  )
}
```

---

## 📱 **What You'll See**

### 🏠 **Property Settings Page**
- **Smart Lock Configuration Section** with three options:
  - 🔐 Automated Smart Lock
  - 👤 Manual Smart Lock
  - 🔑 Traditional Access
- **Instructions field** for custom guest directions
- **Visual indicators** showing the selected lock type

### 🎫 **Reservation Details Page**
- **Complete reservation information** with guest, dates, etc.
- **Smart Lock Access section** showing:
  - Current passcode (if generated)
  - Validity period
  - Manual entry form (for manual locks)
  - Action buttons (Generate, Resend SMS, etc.)

### 📊 **Dashboard Widget**
- **Pending Passcodes list** showing:
  - Urgency indicators (Very Urgent, Urgent, etc.)
  - Guest and property information
  - Quick passcode entry fields
  - One-click "Set Passcode" buttons

### 📧 **Enhanced Template Editor**
- **Smart Lock Variable Selector** with categories:
  - Basic Smart Lock variables
  - Formatted sections
  - Instructions & timing
- **Live template testing** with real reservation data
- **Variable insertion** with click-to-add functionality

---

## 🔗 **Navigation Updates**

Add these navigation links to your existing menu:

```jsx
// In your navigation component
const navigationItems = [
  // Your existing items...

  {
    name: 'Reservations',
    href: '/reservations',
    icon: Calendar,
    children: [
      { name: 'All Reservations', href: '/reservations' },
      { name: 'Pending Passcodes', href: '/reservations/pending-passcodes' }
    ]
  },

  {
    name: 'Properties',
    href: '/properties',
    icon: Home,
    children: [
      { name: 'All Properties', href: '/properties' },
      { name: 'Smart Locks', href: '/smart-locks' }
    ]
  }
]
```

---

## 🎛️ **API Integration Status**

✅ **All API endpoints are ready:**
- Property smart lock settings (GET/PUT)
- Reservation passcode management (CRUD)
- Manual passcode updates
- SMS notification management
- Template variable testing
- Background job monitoring

---

## 🚦 **Quick Start Checklist**

1. ✅ Backend API running with smart lock endpoints
2. ⚠️ **Add PendingPasscodes to dashboard**
3. ⚠️ **Add PropertySmartLockSettings to property pages**
4. ⚠️ **Add ReservationDetails page or integrate component**
5. ⚠️ **Update message template editor**
6. ⚠️ **Add navigation menu items**

---

## 🎯 **User Experience Flow**

### For Automated Smart Lock Properties:
1. Host configures property as "Automated Smart Lock" in settings
2. When reservation is 3 hours from check-in → automatic passcode generation
3. Host receives SMS confirmation
4. Guest receives check-in message with passcode
5. Passcode works on all assigned smart locks

### For Manual Smart Lock Properties:
1. Host configures property as "Manual Smart Lock"
2. When reservation needs passcode → host receives SMS alert
3. Host sets passcode via dashboard or app
4. Guest receives check-in message with passcode

### For Traditional Properties:
1. Host configures property as "Traditional"
2. No passcode generation
3. Custom instructions shown in messages
4. Standard key/lockbox workflow

---

## 🛠️ **Customization Options**

- **Styling**: All components use Tailwind CSS classes - easily customizable
- **Icons**: Using Lucide React icons - replaceable with your icon library
- **Toast notifications**: Using your existing Toaster component
- **API endpoints**: Fully configurable via API_BASE_URL

The integration is designed to work seamlessly with your existing Hostify frontend architecture! 🎉