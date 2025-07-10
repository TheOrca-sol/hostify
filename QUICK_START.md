# Hostify - Quick Start Guide

## 🚀 **New Workflow Overview**

Hostify has been redesigned with the correct user flow:

### **👤 For Hosts:**
1. Login with Firebase (Google/Apple/Microsoft)
2. Create verification links for guests
3. Send links to guests
4. View completed verifications
5. Generate PDF police forms

### **📱 For Guests:**
1. Receive verification link from host
2. Click link (no login required)
3. Upload ID document
4. Review and submit information
5. Done! Host receives the data

---

## 🏃‍♂️ **Quick Setup**

### 1. **Backend Setup**
```bash
cd backend
chmod +x setup-venv.sh
./setup-venv.sh
source venv/bin/activate
pip install -r requirements.txt
```

### 2. **Environment Variables**
Create `backend/.env`:
```env
# Firebase Admin SDK
FIREBASE_ADMIN_SDK_PATH=./app/hostify-797ff-firebase-adminsdk-fbsvc-8e07c589eb.json

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Flask
FLASK_SECRET_KEY=your_secret_key_here
```

Create `frontend/.env`:
```env
# Firebase Web Config
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_auth_domain
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id

# API URL
VITE_API_URL=http://localhost:5000/api
```

### 3. **Database Setup**
```bash
# Run the SQL schema in your Supabase dashboard
cat database/supabase_schema.sql
```

### 4. **Start Development**
```bash
# Terminal 1 - Backend
cd backend && python run.py

# Terminal 2 - Frontend  
cd frontend && npm run dev

# Or use the convenience script
chmod +x run-dev.sh
./run-dev.sh
```

---

## 🔄 **New User Flow**

### **Host Dashboard**
- **Verification Links Tab**: Create and manage guest verification links
- **Verified Guests Tab**: View completed verifications and download PDFs

### **Guest Verification Process**
1. **Link Access**: Guest clicks verification link (e.g., `/verify/abc123...`)
2. **Info Screen**: Welcome page with instructions
3. **Upload**: Drag & drop ID document for OCR processing
4. **Review**: Edit extracted information
5. **Submit**: Complete verification (data goes to host)

---

## 🛠 **API Endpoints**

### **Host Endpoints** (Authentication Required)
- `POST /api/create-verification-link` - Create verification link
- `GET /api/verification-links` - List host's verification links
- `GET /api/guests` - List verified guests
- `DELETE /api/guests/{id}` - Delete guest
- `POST /api/generate-pdf` - Generate police form PDF

### **Guest Endpoints** (Public)
- `GET /api/verify/{token}` - Get verification link info
- `POST /api/verify/{token}/upload` - Upload ID document
- `POST /api/verify/{token}/submit` - Submit verification data

---

## 🔐 **Security Features**

- **Token-based verification**: Secure, time-limited links
- **Row Level Security**: Supabase RLS policies
- **Anonymous guest access**: No accounts needed for guests
- **Automatic expiration**: Links expire after set time
- **One-time use**: Links become invalid after use

---

## 📱 **Example Usage**

### **1. Host creates link:**
```javascript
// Host clicks "Create Verification Link"
{
  "guest_name": "Ahmed Benali",
  "expires_hours": 48
}

// Returns:
{
  "verification_url": "https://hostify.app/verify/abc123def456...",
  "expires_at": "2024-01-15T10:00:00Z"
}
```

### **2. Host sends to guest:**
```
Hi Ahmed! Please complete your ID verification here:
https://hostify.app/verify/abc123def456...
This link expires in 48 hours.
```

### **3. Guest completes verification:**
- Opens link → uploads ID → reviews data → submits
- Host sees the completed verification in their dashboard

---

## 🎯 **Benefits of New Flow**

- ✅ **Better UX**: Guests don't need accounts
- ✅ **More Secure**: Time-limited, one-time use links  
- ✅ **Professional**: Clean separation of host/guest workflows
- ✅ **Scalable**: Hosts can manage multiple guest verifications
- ✅ **Compliant**: Meets legal requirements for Moroccan rentals

Ready to start? Run `./run-dev.sh` and visit `http://localhost:5173`! 