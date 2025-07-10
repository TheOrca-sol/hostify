#!/bin/bash

# Hostify Development Runner
# This script starts both frontend and backend in development mode

echo "🚀 Starting Hostify Development Environment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if npm dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Check if Python virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    echo "📦 Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Python virtual environment already exists"
fi

# Check if environment files exist
if [ ! -f "frontend/.env" ]; then
    echo "⚙️  Creating frontend environment file..."
    cp frontend/.env.example frontend/.env
    echo "Please edit frontend/.env with your Firebase credentials"
fi

if [ ! -f "backend/.env" ]; then
    echo "⚙️  Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env with your credentials"
fi

# Start backend in background
echo "🔧 Starting Flask backend..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend
echo "⚡ Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping development servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

echo "✅ Development environment is running!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait 