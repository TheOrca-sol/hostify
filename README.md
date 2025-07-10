# 🏠 Hostify - Guest ID Verification System

A comprehensive web application for Moroccan rental hosts to verify guest identities and generate legal police forms using OCR technology and automated PDF generation.

## 🌟 **Key Features**

### **🔐 For Hosts (Authentication Required)**
- **Firebase Authentication** - Login with Google, Apple, or Microsoft  
- **Verification Link Management** - Generate secure, time-limited verification links
- **Guest Dashboard** - View all completed verifications
- **PDF Generation** - Download French police forms compliant with Moroccan law
- **Data Management** - Edit and delete guest records

### **📱 For Guests (No Account Required)**
- **One-Click Verification** - Access via secure link from host
- **Smart OCR Processing** - Automatic data extraction from ID documents
- **Mobile-Friendly Interface** - Upload and verify from any device
- **Instant Completion** - Simple 3-step verification process

---

## 🏗️ **Architecture**

### **Frontend (React + Vite)**
- **Framework**: React 18 with Vite for fast development
- **Styling**: TailwindCSS for modern, responsive design
- **Authentication**: Firebase SDK integration
- **State Management**: React hooks and context
- **Routing**: React Router with protected/public routes

### **Backend (Flask + Python)**
- **Framework**: Flask with Blueprint architecture
- **OCR Processing**: Tesseract for ID document text extraction
- **PDF Generation**: ReportLab for French police forms
- **Authentication**: Firebase Admin SDK for token verification
- **File Handling**: Secure temporary file processing

### **Database (Supabase PostgreSQL)**
- **Guest Records**: Complete verification data with timestamps
- **Verification Links**: Secure token management with expiration
- **Row Level Security**: User isolation and data protection
- **Real-time Updates**: Instant synchronization across clients

---

## 🚀 **New Verification Workflow**

### **Step 1: Host Creates Link**
```
Host Dashboard → Create Verification Link → Set expiration → Copy link
```

### **Step 2: Host Sends to Guest**
```
WhatsApp/Email: "Please verify your ID: https://hostify.app/verify/abc123..."
```

### **Step 3: Guest Completes Verification**
```
Click Link → Upload ID → Review Data → Submit → Done!
```

### **Step 4: Host Reviews Results**
```
Dashboard → Verified Guests → Download PDF → Send to Police
```

---

## 🛠️ **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TailwindCSS | Modern, responsive UI |
| **Backend** | Flask + Python | API and business logic |
| **Database** | Supabase PostgreSQL | Data storage with RLS |
| **Authentication** | Firebase Auth | Secure host login |
| **OCR** | Tesseract | ID document processing |
| **PDF** | ReportLab | Police form generation |
| **Hosting** | Vercel + Railway | Scalable deployment |

---

## 📦 **Installation**

### **Prerequisites**
- Node.js 18+ and npm
- Python 3.9+ and pip
- Firebase project with Authentication enabled
- Supabase project with PostgreSQL database

### **Quick Start**
```bash
# Clone repository
git clone https://github.com/your-username/hostify.git
cd hostify

# Setup backend
cd backend
chmod +x setup-venv.sh
./setup-venv.sh
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Configure environment variables (see setup.md)
# Run development servers
cd ..
chmod +x run-dev.sh
./run-dev.sh
```

### **Environment Configuration**
See [setup.md](setup.md) for detailed environment variable configuration.

---

## 🔄 **API Documentation**

### **Host Endpoints** (Authentication Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/create-verification-link` | Create guest verification link |
| `GET` | `/api/verification-links` | List host's verification links |
| `GET` | `/api/guests` | Get verified guests |
| `DELETE` | `/api/guests/{id}` | Delete guest record |
| `POST` | `/api/generate-pdf` | Generate police form PDF |

### **Guest Endpoints** (Public Access)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/verify/{token}` | Get verification link info |
| `POST` | `/api/verify/{token}/upload` | Upload ID document |
| `POST` | `/api/verify/{token}/submit` | Submit verification data |

---

## 🔐 **Security Features**

- **🛡️ Token-based verification** with automatic expiration
- **🔒 Row Level Security** in Supabase for data isolation
- **🚫 Anonymous guest access** (no accounts required)
- **⏰ Time-limited links** prevent unauthorized access
- **🔑 One-time use tokens** prevent replay attacks
- **🔥 Firebase Admin SDK** for secure authentication

---

## 📱 **Mobile Support**

- **📸 Camera integration** for direct ID photo capture
- **👆 Touch-friendly interface** optimized for smartphones
- **📶 Offline capability** for form completion
- **🔄 Auto-save** prevents data loss
- **📏 Responsive design** adapts to all screen sizes

---

## 🌍 **Internationalization**

- **🇫🇷 French PDF generation** for Moroccan police compliance
- **🇲🇦 Arabic text support** for Moroccan ID cards
- **🌐 Multi-language UI** (French/Arabic/English)
- **🗓️ Date format localization** for different regions

---

## 🚀 **Deployment**

### **Production Environment**
```bash
# Build frontend
cd frontend && npm run build

# Configure production environment variables
# Deploy to your preferred hosting platform
```

### **Recommended Hosting**
- **Frontend**: Vercel or Netlify
- **Backend**: Railway, Heroku, or DigitalOcean
- **Database**: Supabase (managed PostgreSQL)
- **Storage**: Supabase Storage or AWS S3

---

## 📊 **Project Structure**

```
hostify/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route components
│   │   ├── services/        # API and auth services
│   │   └── App.jsx          # Main application
│   └── package.json
├── backend/                  # Flask API
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── utils/           # Helper functions
│   │   └── main.py          # Flask application
│   ├── requirements.txt
│   └── run.py
├── database/
│   └── supabase_schema.sql  # Database schema
└── docs/                    # Documentation
```

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

- **📚 Documentation**: [Full setup guide](setup.md)
- **🚀 Quick start**: [Quick start guide](QUICK_START.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/hostify/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-username/hostify/discussions)

---

## 🎯 **Roadmap**

- [ ] **Multi-property support** for large hosts
- [ ] **Bulk verification** for group bookings
- [ ] **QR code generation** for contactless check-in
- [ ] **Mobile app** for iOS and Android
- [ ] **Integration APIs** for booking platforms
- [ ] **Advanced analytics** and reporting

---

**Made with ❤️ for Moroccan rental hosts** 