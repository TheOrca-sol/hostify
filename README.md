# 🏠 Hostify - Automated Property Management Platform

Hostify is a comprehensive property management system designed to automate the most time-consuming tasks for rental hosts. It handles iCal sync, guest verification, and automated, event-driven communication, allowing you to focus on providing a great guest experience.

## 🌟 Core Features

### 🏢 Property & Reservation Management
- **Multi-Property Support:** Manage all your properties from a single dashboard.
- **iCal Sync:** Automatically syncs reservations from platforms like Airbnb, Booking.com, and Vrbo.
- **Smart Parsing:** Intelligently parses iCal data to identify and ignore blocked periods, extracting guest confirmation codes and partial phone numbers.
- **Search & Pagination:** Easily search and navigate through all your reservations and guests.

### 🔐 Guest Verification
- **Automated Link Sending:** Manually trigger the verification process, which then kicks off all other automations.
- **Document Upload & OCR:** Guests upload their ID documents, and the system uses OCR to automatically extract their information.
- **Generic Document Support:** The OCR is designed to work with a wide variety of international ID cards and passports.
- **Host Review:** Securely view uploaded documents to manually verify guest information.

### 💬 Automated Communication Engine
- **Customizable Message Templates:** Create and manage a full suite of SMS templates for every stage of the guest journey.
- **Powerful Automation Rules:** Build rules to schedule messages based on triggers like "2 days before check-in" or "4 hours after check-out."
- **Centralized Control:** The automation sequence for a guest is triggered only when you manually send the verification link, giving you full control.
- **Background Worker:** A reliable background process runs continuously to send scheduled messages at the correct time.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TailwindCSS | Modern, responsive UI |
| **Backend** | Flask + SQLAlchemy | API and business logic |
| **Database** | PostgreSQL | Data storage |
| **Auth** | Firebase Auth | User authentication |
| **OCR** | Tesseract | Document processing |
| **SMS** | Twilio | SMS notifications |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ and Node.js 18+
- A PostgreSQL database
- A Firebase project for authentication
- A Twilio account for sending SMS

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

## 📊 Project Structure
```
hostify/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── utils/
│   │   └── models.py
│   ├── migrations/
│   ├── scripts/  # Standalone scripts (e.g., background worker)
│   └── run.py
└── README.md
```