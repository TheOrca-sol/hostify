# 🏠 Hostify - Complete Property Management Platform

A comprehensive property management system for Moroccan rental hosts that handles guest verification, contract generation, digital signatures, automated messaging, and legal compliance.

## 🌟 **Key Features**

### **🏢 Property Management**
- **Multi-property Support** - Manage unlimited properties
- **Property Details** - Track addresses, amenities, and settings
- **Calendar Sync** - Automatic iCal synchronization with booking platforms
- **Occupancy Overview** - Visual calendar of all reservations

### **📋 Reservation Management**
- **Auto-Sync** - Import bookings from Airbnb, Booking.com, etc.
- **Guest Assignment** - Link guests to reservations
- **Status Tracking** - Monitor confirmed, pending, and completed stays
- **Calendar View** - Visual timeline of all bookings

### **🔐 Guest Verification**
- **Automated Process** - Send verification links to guests
- **Document Upload** - OCR processing of ID documents
- **Data Validation** - Verify guest information
- **Status Tracking** - Monitor verification progress

### **📄 Contract Management**
- **Template System** - Customize contract templates
- **Auto-Generation** - Create contracts from verified guest data
- **Digital Signatures** - Secure online contract signing
- **PDF Generation** - Professional contract documents
- **Legal Compliance** - Meet Moroccan rental regulations

### **💬 Communication Center**
- **Message Templates** - Pre-built templates for common scenarios
- **Automated Messaging** - Schedule messages based on booking events
- **Multi-Channel** - Email and SMS support
- **Guest Timeline** - Track all communications
- **Language Support** - Templates in Arabic, French, and English

### **📱 Host Dashboard**
- **Overview** - Quick stats and recent activity
- **Property Cards** - Status of each property
- **Task Management** - Track pending verifications and contracts
- **Communication Log** - Recent messages and notifications

---

## 🏗️ **Architecture**

### **Frontend (React + Vite)**
- **Framework**: React 18 with Vite
- **Styling**: TailwindCSS for modern UI
- **State Management**: React Context + Hooks
- **Routing**: React Router with protected routes
- **Components**: Reusable UI library

### **Backend (Flask + Python)**
- **Framework**: Flask with Blueprint architecture
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Firebase Admin SDK
- **Background Tasks**: Redis + Celery for scheduling
- **File Processing**: 
  - Tesseract for OCR
  - ReportLab for PDF generation
  - Cloud storage for documents

### **Integrations**
- **Authentication**: Firebase (Google, Apple, Microsoft)
- **Database**: Supabase PostgreSQL
- **Storage**: Firebase Storage
- **Messaging**: Twilio (SMS) + SendGrid (Email)
- **Calendar**: iCal synchronization
- **Signatures**: Digital signature processing

---

## 🔄 **Core Workflows**

### **1. Property Setup**
```
Add Property → Configure Settings → Set Contract Templates → Enable Auto-sync
```

### **2. Reservation Management**
```
Auto-sync Bookings → Assign Guests → Schedule Messages → Track Status
```

### **3. Guest Verification**
```
Send Link → Guest Uploads ID → OCR Processing → Data Verification
```

### **4. Contract Process**
```
Generate Contract → Guest Reviews → Digital Signature → Store Document
```

### **5. Communication Flow**
```
Create Templates → Set Triggers → Automated Sending → Track Responses
```

---

## 🛠️ **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TailwindCSS | Modern, responsive UI |
| **Backend** | Flask + SQLAlchemy | API and business logic |
| **Database** | Supabase PostgreSQL | Data storage with RLS |
| **Auth** | Firebase Auth | User authentication |
| **Tasks** | Redis + Celery | Background processing |
| **OCR** | Tesseract | Document processing |
| **PDF** | ReportLab | Contract generation |
| **Storage** | Firebase Storage | Document storage |
| **Email** | SendGrid | Email communications |
| **SMS** | Twilio | SMS notifications |

---

## 📊 **Project Structure**

```
hostify/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── pages/          # Route components
│   │   ├── services/       # API and auth services
│   │   └── App.jsx         # Main application
│   └── package.json
├── backend/                 # Flask API
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   │   ├── properties.py   # Property management
│   │   │   ├── reservations.py # Reservation handling
│   │   │   ├── guests.py       # Guest management
│   │   │   ├── contracts.py    # Contract operations
│   │   │   ├── messages.py     # Communication system
│   │   │   └── verification.py # ID verification
│   │   ├── utils/          # Helper functions
│   │   │   ├── auth.py        # Authentication
│   │   │   ├── pdf.py         # PDF generation
│   │   │   ├── ocr.py         # Document processing
│   │   │   ├── messaging.py   # Communication
│   │   │   └── calendar_sync.py # iCal sync
│   │   └── models.py       # Database models
│   ├── migrations/         # Database migrations
│   ├── requirements.txt
│   └── run.py
└── docs/                   # Documentation
```

---

## 🎯 **Roadmap**

- [ ] **Booking Management** - Direct booking system
- [ ] **Financial Module** - Payment processing and reporting
- [ ] **Maintenance Module** - Track property maintenance
- [ ] **Owner Portal** - For property owners
- [ ] **Mobile Apps** - Native iOS and Android
- [ ] **API Integration** - Public API for third-party integration

---

**Built for Professional Rental Property Management** 🏢 