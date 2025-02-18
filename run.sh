#!/bin/bash

# Default ports
FRONTEND_PORT=4200
BACKEND_PORT=8000

# Function to check if a port is in use
check_port() {
    lsof -i ":$1" >/dev/null 2>&1
    return $?
}

# Function to find next available port
find_next_port() {
    local port=$1
    while check_port $port; do
        port=$((port + 1))
    done
    echo "$port"
}

# Function to cleanup background processes on script exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT

# Find available ports
FRONTEND_PORT=$(find_next_port $FRONTEND_PORT)
echo "Using frontend port: $FRONTEND_PORT"
BACKEND_PORT=$(find_next_port $BACKEND_PORT)
echo "Using backend port: $BACKEND_PORT"

# Start the backend server
echo "Starting backend server..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" &
cd ..

# Start the frontend server
echo "Starting frontend server..."
cd frontend/exam-o-matic
npm start -- --port "$FRONTEND_PORT" &

echo -e "\nServices are starting..."
echo "Frontend will be available at: http://localhost:$FRONTEND_PORT"
echo "Backend will be available at: http://localhost:$BACKEND_PORT"
echo "Press Ctrl+C to stop both services"

# Wait for any background process to exit
wait