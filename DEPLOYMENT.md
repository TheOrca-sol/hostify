# 🚀 Hostify Deployment Guide

## 📋 Prerequisites
- GitHub repository
- Railway account
- Vercel account  
- Supabase database (already set up)

## 🚂 Railway Backend Deployment

### 1. Create Railway Project
1. Go to [Railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `hostify` repository
5. Set root directory to `backend/`

### 2. Environment Variables
Add these environment variables in Railway dashboard:

```bash
DATABASE_URL=your_supabase_connection_string
SECRET_KEY=generate_a_strong_secret_key_here
FLASK_ENV=production
FRONTEND_URL=https://your-vercel-app.vercel.app

# Firebase
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----"
FIREBASE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

### 3. Deploy
- Railway will automatically build and deploy your backend
- Note your Railway app URL (e.g., `https://your-app.railway.app`)

## ⚡ Vercel Frontend Deployment

### 1. Create Vercel Project
1. Go to [Vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Set root directory to `frontend/`
5. Framework preset: "Vite"

### 2. Environment Variables
Add these in Vercel dashboard:

```bash
VITE_API_BASE_URL=https://your-railway-app.railway.app/api
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-firebase-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456789
```

### 3. Deploy
- Vercel will automatically build and deploy your frontend
- Note your Vercel app URL

## 🔄 Update CORS
After getting your Vercel URL, update the CORS configuration in Railway:
```bash
FRONTEND_URL=https://your-actual-vercel-url.vercel.app
```

## ✅ Verification Checklist
- [ ] Backend health check: `https://your-railway-app.railway.app/health`
- [ ] Frontend loads: `https://your-vercel-app.vercel.app`
- [ ] API calls work from frontend to backend
- [ ] Firebase authentication works
- [ ] Database operations work
- [ ] Message worker is running

## 🐛 Troubleshooting
- **CORS errors**: Check FRONTEND_URL in Railway matches Vercel URL
- **API errors**: Verify all environment variables are set
- **Database errors**: Check DATABASE_URL is correct Supabase connection string
- **Auth errors**: Verify Firebase environment variables

## 📊 Monitoring
- Railway: Check logs in Railway dashboard
- Vercel: Check function logs in Vercel dashboard
- Database: Monitor queries in Supabase dashboard