# 🏠 Hostify - Smart Property Management Platform

Hostify is a comprehensive multi-role property management system with intelligent **smart lock automation**, designed to eliminate the most time-consuming tasks for rental hosts, co-hosts, agencies, and service teams. It features automated passcode generation, guest verification, smart communication, team management, contract handling, and advanced analytics - allowing you to focus on providing exceptional guest experiences.

## 🌟 Core Features

### 🔐 Smart Lock Automation & Access Management
- **TTLock Integration:** Automated passcode generation 3 hours before check-in with real-time sync
- **Multi-Access Types:** Support for TTLock automated, manual smart locks, and traditional key access
- **Intelligent Timing:** Passcodes valid from 1 hour before check-in to 1 hour after check-out
- **Host Notifications:** SMS alerts for passcode generation and manual entry requirements
- **Dashboard Widgets:** Real-time pending passcode alerts with urgency indicators
- **Property Configuration:** Per-property smart lock type settings with custom guest instructions

### 🏢 Property & Reservation Management
- **Multi-Property Support:** Manage all your properties from a single unified dashboard
- **iCal Sync:** Automatically syncs reservations from platforms like Airbnb, Booking.com, and Vrbo
- **Smart Parsing:** Intelligently parses iCal data to identify and ignore blocked periods, extracting guest confirmation codes and partial phone numbers
- **Advanced Search & Filtering:** Easily search and navigate through all your reservations and guests with powerful filters
- **Occupancy Analytics:** Interactive charts and calendar views showing property utilization rates with period selection (week/month/quarter/year)
- **Passcode Status Tracking:** Visual indicators showing smart lock passcode status across all reservations

### 👥 Multi-Role Team Management
- **Flexible Role System:** Support for property owners, co-hosts, agencies, cleaners, and maintenance workers.
- **Unified Workspace:** Team members see all assigned properties with role-based permissions and access control.
- **Dual Invitation Methods:** Email invitations for managers (co-hosts/agencies) and SMS invitations for service workers (cleaners/maintenance).
- **International Phone Support:** Country code selector with automatic Moroccan (+212) number formatting.
- **Permission Matrix:** Granular control over team member access to features like financials, pricing, and property management.

### 🔐 Guest Verification & Contracts
- **Automated Verification Links:** Manually trigger the verification process, which then kicks off all other automations.
- **Document Upload & OCR:** Guests upload their ID documents, and the system uses OCR to automatically extract their information.
- **Generic Document Support:** The OCR is designed to work with a wide variety of international ID cards and passports.
- **Digital Contract Generation:** Automated PDF contract creation with embedded host and guest signatures.
- **Contract Signing Flow:** Secure digital signature capture and contract management system.
- **Host Review:** Securely view uploaded documents to manually verify guest information.

### 💬 Smart Communication Engine
- **Smart Lock Variables:** Advanced message templates with dynamic smart lock information (`{smart_lock_passcode}`, `{lock_passcode_section}`)
- **Live Template Testing:** Real-time template preview with actual reservation data
- **Variable Categories:** Organized smart lock, guest, property, and timing variables
- **Customizable Templates:** Full suite of SMS templates for every stage of the guest journey
- **Powerful Automation Rules:** Schedule messages based on triggers like "2 days before check-in" or "4 hours after check-out"
- **Centralized Control:** Manual trigger system gives you complete control over guest communication flow
- **Background Workers:** Reliable dedicated processes for message delivery and smart lock automation
- **SMS Authentication:** Phone-based login system for service workers with verification codes

### 📊 Advanced Analytics & Insights
- **Interactive Occupancy Dashboard:** Visual charts and calendar heatmaps showing property utilization.
- **Property Performance Metrics:** Individual property breakdowns with booking rates and revenue insights.
- **Period Comparison:** Week, month, quarter, and yearly occupancy analysis with trend tracking.
- **Team Activity Monitoring:** Track team member actions and property access across your portfolio.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TailwindCSS | Modern, responsive UI with smart lock management |
| **Backend** | Flask + SQLAlchemy | API and business logic with smart lock automation |
| **Database** | PostgreSQL | Data storage with UUID primary keys and smart lock models |
| **Auth** | Firebase Auth | Multi-method authentication (Google, Email, SMS) |
| **Smart Locks** | TTLock API | Automated passcode generation and lock management |
| **OCR** | Tesseract | Document processing and data extraction |
| **SMS** | Twilio | SMS notifications, phone authentication, and smart lock alerts |
| **PDF Generation** | ReportLab + Pillow | Contract generation with digital signatures |
| **Background Jobs** | Dedicated Worker Processes | Smart lock automation, calendar sync, message delivery |
| **Migrations** | Flask-Migrate (Alembic) | Database schema management |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ and Node.js 18+
- A PostgreSQL database
- A Firebase project for authentication (Google, Email/Password, Phone auth)
- A Twilio account for sending SMS and phone verification
- Tesseract OCR engine installed on your system

### 1. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file and configure your environment variables
# (See .env.example for a template)
cp .env.example .env

# Run the database migrations
flask db upgrade

# Run the backfill scripts to create default templates for existing users
python scripts/backfill_default_templates.py
python scripts/backfill_contract_templates.py
```

### 2. Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Create a .env file and add your Firebase configuration
# (See .env.example for a template)
cp .env.example .env
```

### 3. Running the Application
You will need to run three processes in separate terminals:

**Terminal 1: Run the Backend API**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Terminal 2: Run the Frontend Dev Server**
```bash
cd frontend
npm run dev
```

**Terminal 3: Run the Background Workers**
```bash
cd backend
source venv/bin/activate
python scripts/start_workers.py
```

This starts three dedicated worker processes:
- **Smart Lock Automation** (5 min intervals) - Passcode generation and cleanup
- **Calendar Sync** (5 min intervals) - Property reservation synchronization
- **Message Delivery** (60 sec intervals) - Scheduled SMS notifications

The application will be available at `http://localhost:3000` with full smart lock automation.

---

## 🔐 Authentication Methods

Hostify supports multiple authentication methods to accommodate different user types:

### 🌐 **Web Users (Owners, Co-hosts, Agencies)**
- **Google Sign-In**: One-click authentication with Google accounts
- **Email/Password**: Traditional email-based registration and login
- **Apple Sign-In**: iOS-friendly authentication (optional)

### 📱 **Mobile Users (Cleaners, Maintenance Workers)**
- **SMS Authentication**: Phone number-based login with verification codes
- **International Support**: Country code selection with automatic formatting
- **Simplified Flow**: Designed for users with varying technical literacy

### 👥 **Team Invitation System**
- **Email Invitations**: Professional invites for managers and co-hosts
- **SMS Invitations**: Text-based invites for service workers
- **Flexible Permissions**: Granular control over team member access
- **Multi-Property Support**: Invite to specific properties or entire portfolio

---

## 📊 Analytics & Insights

### 📈 **Occupancy Analytics**
- **Interactive Charts**: Visual representation of property utilization rates
- **Calendar Heatmap**: Day-by-day occupancy visualization with color coding
- **Period Selection**: Analyze by week, month, quarter, or year
- **Property Comparison**: Individual property performance breakdowns
- **Trend Analysis**: Historical data with future booking projections

### 🎯 **Key Metrics**
- **Overall Occupancy Rate**: Portfolio-wide utilization percentage
- **Property Performance**: Individual property booking rates and revenue
- **Seasonal Trends**: Identify peak and off-peak periods
- **Team Activity**: Monitor team member actions and property access

---

## 📊 Project Structure
```
hostify/
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── PhoneInput.jsx                  # International phone input
│   │   │   ├── SignatureCapture.jsx            # Digital signature capture
│   │   │   ├── OccupancyCalendar.jsx           # Interactive occupancy heatmap
│   │   │   ├── PropertyOccupancyChart.jsx      # Property performance charts
│   │   │   ├── PendingPasscodes.jsx            # Smart lock dashboard widget
│   │   │   ├── PropertySmartLockSettings.jsx   # Property smart lock configuration
│   │   │   ├── ReservationPasscodeManager.jsx  # Individual reservation passcode management
│   │   │   ├── EnhancedMessageTemplateEditor.jsx # Template editor with smart lock variables
│   │   │   └── SmartLockVariableSelector.jsx   # Smart lock template variable helper
│   │   ├── pages/              # Main application pages
│   │   │   ├── Dashboard.jsx           # Multi-role dashboard with pending passcode alerts
│   │   │   ├── TeamManagement.jsx      # Team invitation and management
│   │   │   ├── InvitationAcceptance.jsx # Team invitation landing page
│   │   │   ├── ContractSigning.jsx     # Digital contract signing
│   │   │   ├── ProfileSetup.jsx        # User profile with signature
│   │   │   ├── ReservationDetails.jsx  # Comprehensive reservation and passcode management
│   │   │   ├── PropertyLocks.jsx       # Property smart lock configuration page
│   │   │   └── MessageTemplates.jsx    # Enhanced template management with smart lock variables
│   │   ├── services/           # API and authentication services
│   │   │   ├── api.js                  # Centralized API calls with smart lock endpoints
│   │   │   └── auth.jsx                # Multi-method Firebase auth
│   │   └── App.jsx             # Main routing with smart lock pages
├── backend/
│   ├── app/
│   │   ├── routes/             # API endpoints
│   │   │   ├── team.py                 # Team management APIs
│   │   │   ├── sms_auth.py            # SMS authentication APIs
│   │   │   ├── contracts.py           # Contract generation and signing
│   │   │   ├── dashboard.py           # Analytics and occupancy data
│   │   │   ├── verification.py        # Guest verification flow
│   │   │   ├── smart_locks.py         # TTLock integration and device management
│   │   │   ├── reservation_passcodes.py # Smart lock passcode management APIs
│   │   │   └── properties.py          # Property management with smart lock settings
│   │   ├── services/           # Business logic services
│   │   │   ├── team_management.py     # Team invitation and permissions
│   │   │   ├── sms_auth.py           # SMS verification service
│   │   │   ├── pdf_generator.py      # Contract PDF generation
│   │   │   ├── passcode_service.py   # Smart lock passcode generation and management
│   │   │   ├── ttlock_service.py     # TTLock API integration service
│   │   │   └── message_template_service.py # Template processing with smart lock variables
│   │   ├── utils/              # Business logic utilities
│   │   │   ├── database.py           # Occupancy calculations
│   │   │   ├── automation.py         # Message automation engine
│   │   │   └── messaging.py          # SMS delivery with smart lock integration
│   │   └── models.py           # SQLAlchemy database models with smart lock tables
│   ├── migrations/             # Database schema migrations
│   ├── scripts/                # Dedicated background worker processes
│   │   ├── start_workers.py          # Worker process manager
│   │   ├── smart_lock_automation.py  # Smart lock passcode generation worker
│   │   ├── send_scheduled_messages.py # Message delivery worker
│   │   └── sync_calendars.py         # Calendar synchronization worker
│   ├── contracts/              # Generated contract files
│   ├── uploads/                # Guest document uploads
│   └── run.py                  # Flask application entry point
└── README.md
```

## 🎯 Key Database Models

- **User**: Multi-role user accounts with signatures, phone numbers, and TTLock credentials
- **Property**: Property information with team management and smart lock configuration
- **PropertyTeamMember**: Role-based team member assignments
- **TeamInvitation**: Email and SMS invitation tracking
- **PhoneVerification**: SMS authentication codes and verification
- **Reservation**: Guest bookings with iCal sync and passcode integration
- **ReservationPasscode**: Smart lock passcodes with validity periods and generation methods
- **SmartLock**: TTLock device information and property assignments
- **AccessCode**: Individual smart lock passcodes with usage tracking
- **AccessLog**: Smart lock access history and audit trail
- **Guest**: Guest information with document verification
- **Contract**: Digital contracts with signature management
- **MessageTemplate**: Automated communication templates with smart lock variables

---

## 🔐 Smart Lock Features

### 🎯 **Property-Level Configuration**
- **TTLock Automated**: Full automation with 3-hour advance passcode generation
- **Manual Smart Lock**: Dashboard-driven passcode entry with SMS alerts
- **Traditional Access**: Custom instructions for key/lockbox access

### 📱 **Dashboard Widgets**
- **Pending Passcodes**: Real-time alerts with urgency indicators (Very Urgent < 6hrs, Urgent < 12hrs)
- **Passcode Status**: Visual indicators across all reservation listings
- **One-Click Actions**: Quick passcode entry and guest notifications

### 💬 **Smart Template Variables**
- `{smart_lock_passcode}` - The actual numeric passcode
- `{lock_passcode_section}` - Complete formatted passcode section
- `{smart_lock_instructions}` - Custom property access instructions
- `{passcode_valid_from}` / `{passcode_valid_until}` - Validity timing
- `{smart_lock_type}` - Property access method type

### 🤖 **Background Automation**
- **Automatic Generation**: TTLock passcodes created 3 hours before check-in
- **SMS Notifications**: Hosts receive alerts for both automated and manual passcodes
- **Cleanup Processing**: Expired passcodes automatically marked and cleaned up
- **Dedicated Workers**: Separate processes for reliability and scaling

---

## 🚀 **Getting Started with Smart Locks**

1. **Configure Property**: Set smart lock type in property settings
2. **Connect TTLock**: Add TTLock credentials for automated properties
3. **Create Templates**: Use smart lock variables in your message templates
4. **Start Workers**: Run background processes for automation
5. **Monitor Dashboard**: Track pending passcodes and guest access

The smart lock system integrates seamlessly with your existing workflow, providing automated access management without disrupting your current guest communication process.