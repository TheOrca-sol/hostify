# Hostify Setup Guide

## Quick Start

Follow these steps to get Hostify running on your local machine:

### 1. Install Dependencies

#### System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara python3-pip nodejs npm

# macOS
brew install tesseract tesseract-lang node python3

# Windows
# Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
# Install Node.js from: https://nodejs.org/
# Install Python from: https://python.org/
```

### 2. Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install Node.js dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your Firebase credentials
nano .env

# Go back to root
cd ..
```

### 3. Setup Backend

#### Option 1: Quick Setup (Recommended)
```bash
# Navigate to backend and run setup script
cd backend
./setup-venv.sh
cd ..
```

#### Option 2: Manual Setup
```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Go back to root
cd ..
```

### 4. Setup Database

1. Create a Supabase project at https://supabase.com
2. In the SQL Editor, run the schema from `database/supabase_schema.sql`
3. Get your Supabase URL and anon key
4. Update your backend `.env` file

### 5. Setup Firebase

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication with Google, Apple, and Microsoft providers
3. Generate Firebase Admin SDK credentials
4. Update both `.env` files with your Firebase credentials

### 6. Run the Application

#### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate
python run.py
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to use the application!

## Configuration Details

### Firebase Setup

1. **Create Project**: Go to Firebase Console and create a new project
2. **Enable Authentication**: 
   - Go to Authentication → Sign-in method
   - Enable Google, Apple, and Microsoft providers
3. **Web App Config**:
   - Go to Project Settings → General → Your apps
   - Add a web app and copy the config
4. **Admin SDK**:
   - Go to Project Settings → Service accounts
   - Generate new private key
   - Copy the JSON content

### Supabase Setup

1. **Create Project**: Go to Supabase and create a new project
2. **Run Schema**: Execute the SQL from `database/supabase_schema.sql`
3. **Get Credentials**: 
   - Go to Settings → API
   - Copy URL and anon key

### Environment Variables

#### Frontend (.env)
```env
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=your-app-id
VITE_API_BASE_URL=http://localhost:5000
```

#### Backend (backend/.env)
```env
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
FIREBASE_ADMIN_SDK_JSON={"type": "service_account", ...}
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**:
   - Ensure Tesseract is installed and in PATH
   - On Windows, add to system PATH

2. **Firebase authentication fails**:
   - Check that providers are enabled in Firebase Console
   - Verify domain is added to authorized domains

3. **Database connection fails**:
   - Verify Supabase credentials
   - Check if RLS policies are set up correctly

4. **CORS errors**:
   - Ensure Flask-CORS is properly configured
   - Check that frontend URL is allowed

### Development Tips

- Use `npm run dev` for hot reload in development
- Use `python run.py` for backend development with auto-reload
- Check browser console for detailed error messages
- Use Firebase Authentication emulator for local testing

## Production Deployment

### Frontend (Vercel/Netlify)

1. Build the frontend: `npm run build`
2. Deploy the `dist` folder
3. Set environment variables in deployment settings

### Backend (Railway/Heroku)

1. Create a `requirements.txt` file
2. Set environment variables
3. Deploy the backend folder

### Database

- Supabase is production-ready
- Configure Row Level Security policies
- Set up proper indexes for performance

## Support

If you encounter issues:

1. Check the troubleshooting section
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check the console for error messages

For additional help, refer to the README.md file or create an issue in the repository. 