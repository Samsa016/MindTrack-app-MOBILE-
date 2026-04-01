#!/usr/bin/env bash

# Function to handle graceful shutdown
cleanup() {
    echo ""
    echo "========================================="
    echo "🛑 Shutting down MindTrack development servers..."
    echo "========================================="
    
    # Kill the background node process if it exists
    if [ -n "$FRONTEND_PID" ]; then
        echo "Killing Next.js frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill the background uvicorn process if it exists
    if [ -n "$BACKEND_PID" ]; then
        echo "Killing FastAPI backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    echo "Stops are sent. To stop the database, run: docker-compose stop db"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "========================================="
echo "🚀 Starting MindTrack Local Development Mode"
echo "========================================="

# 1. Start PostgreSQL Database
echo ""
echo "📦 Starting Database via Docker Compose..."
docker-compose up -d db

# 2. Setup and run Backend
echo ""
echo "🐍 Setting up Python Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
echo "Installing Python dependencies (checking)..."
pip install -r requirements.txt -q

# Start Uvicorn in the background
echo "Starting FastAPI on http://localhost:8000 ..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Go back to root
cd ..

# 3. Setup and run Frontend
echo ""
echo "⚛️  Setting up React Frontend..."
cd frontend

# Install Node modules if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js packages..."
    npm install
fi

# Start Next.js in the background
echo "Starting Next.js on http://localhost:3000 ..."
npm run dev &
FRONTEND_PID=$!

# Go back to root
cd ..

echo ""
echo "======================================================"
echo "✅ All servers running concurrently!"
echo "   🟢 Frontend: http://localhost:3000"
echo "   🟢 Backend:  http://localhost:8000"
echo "   🟢 Database: localhost:5432 (PostgreSQL)"
echo "⚠️  Press Ctrl+C to stop all servers."
echo "======================================================"

# Wait for background processes to finish (which won't happen unless error)
wait $BACKEND_PID
wait $FRONTEND_PID
