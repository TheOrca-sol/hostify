# 🏠 Hostify - Automated Property Management Platform

Hostify is a comprehensive multi-role property management system designed to automate the most time-consuming tasks for rental hosts, co-hosts, agencies, and service teams. It handles iCal sync, guest verification, automated communication, team management, contract generation, and provides advanced analytics - allowing you to focus on providing a great guest experience.

## 🌟 Core Features

### 🏢 Property & Reservation Management
- **Multi-Property Support:** Manage all your properties from a single unified dashboard.
- **iCal Sync:** Automatically syncs reservations from platforms like Airbnb, Booking.com, and Vrbo.
- **Smart Parsing:** Intelligently parses iCal data to identify and ignore blocked periods, extracting guest confirmation codes and partial phone numbers.
- **Advanced Search & Filtering:** Easily search and navigate through all your reservations and guests with powerful filters.
- **Occupancy Analytics:** Interactive charts and calendar views showing property utilization rates with period selection (week/month/quarter/year).

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

### 💬 Automated Communication Engine
- **Customizable Message Templates:** Create and manage a full suite of SMS templates for every stage of the guest journey.
- **Powerful Automation Rules:** Build rules to schedule messages based on triggers like "2 days before check-in" or "4 hours after check-out."
- **Centralized Control:** The automation sequence for a guest is triggered only when you manually send the verification link, giving you full control.
- **Background Worker:** A reliable background process runs continuously to send scheduled messages at the correct time.
- **SMS Authentication:** Phone-based login system for service workers with verification codes.

### 📊 Advanced Analytics & Insights
- **Interactive Occupancy Dashboard:** Visual charts and calendar heatmaps showing property utilization.
- **Property Performance Metrics:** Individual property breakdowns with booking rates and revenue insights.
- **Period Comparison:** Week, month, quarter, and yearly occupancy analysis with trend tracking.
- **Team Activity Monitoring:** Track team member actions and property access across your portfolio.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TailwindCSS | Modern, responsive UI with interactive charts |
| **Backend** | Flask + SQLAlchemy | API and business logic with multi-role support |
| **Database** | PostgreSQL | Data storage with UUID primary keys |
| **Auth** | Firebase Auth | Multi-method authentication (Google, Email, SMS) |
| **OCR** | Tesseract | Document processing and data extraction |
| **SMS** | Twilio | SMS notifications and phone authentication |
| **PDF Generation** | ReportLab + Pillow | Contract generation with digital signatures |
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
flask run
```

**Terminal 2: Run the Frontend Dev Server**
```bash
cd frontend
npm run dev
```

**Terminal 3: Run the Automation Engine**
```bash
cd backend
source venv/bin/activate
python scripts/send_scheduled_messages.py
```

The application will now be available at `http://localhost:3000`.

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
│   │   │   ├── PhoneInput.jsx          # International phone input
│   │   │   ├── SignatureCapture.jsx    # Digital signature capture
│   │   │   ├── OccupancyCalendar.jsx   # Interactive occupancy heatmap
│   │   │   └── PropertyOccupancyChart.jsx # Property performance charts
│   │   ├── pages/              # Main application pages
│   │   │   ├── Dashboard.jsx           # Multi-role dashboard with analytics
│   │   │   ├── TeamManagement.jsx      # Team invitation and management
│   │   │   ├── InvitationAcceptance.jsx # Team invitation landing page
│   │   │   ├── ContractSigning.jsx     # Digital contract signing
│   │   │   └── ProfileSetup.jsx        # User profile with signature
│   │   ├── services/           # API and authentication services
│   │   │   ├── api.js                  # Centralized API calls
│   │   │   └── auth.jsx                # Multi-method Firebase auth
│   │   └── App.jsx             # Main routing and app structure
├── backend/
│   ├── app/
│   │   ├── routes/             # API endpoints
│   │   │   ├── team.py                 # Team management APIs
│   │   │   ├── sms_auth.py            # SMS authentication APIs
│   │   │   ├── contracts.py           # Contract generation and signing
│   │   │   ├── dashboard.py           # Analytics and occupancy data
│   │   │   └── verification.py        # Guest verification flow
│   │   ├── utils/              # Business logic utilities
│   │   │   ├── team_management.py     # Team invitation and permissions
│   │   │   ├── sms_auth.py           # SMS verification service
│   │   │   ├── pdf_generator.py      # Contract PDF generation
│   │   │   ├── database.py           # Occupancy calculations
│   │   │   └── automation.py         # Message automation engine
│   │   └── models.py           # SQLAlchemy database models
│   ├── migrations/             # Database schema migrations
│   ├── scripts/                # Standalone background scripts
│   │   └── send_scheduled_messages.py  # Automation worker
│   ├── contracts/              # Generated contract files
│   ├── uploads/                # Guest document uploads
│   └── run.py                  # Flask application entry point
└── README.md
```

## 🎯 Key Database Models

- **User**: Multi-role user accounts with signatures and phone numbers
- **Property**: Property information with team management
- **PropertyTeamMember**: Role-based team member assignments
- **TeamInvitation**: Email and SMS invitation tracking
- **PhoneVerification**: SMS authentication codes and verification
- **Reservation**: Guest bookings with iCal sync
- **Guest**: Guest information with document verification
- **Contract**: Digital contracts with signature management
- **MessageTemplate**: Automated communication templates