#!/bin/bash

# Local development runner script

echo "🚀 Starting California Motion Writer (Local Development)"
echo "======================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "⚠️  Warning: Python $required_version or higher is recommended (you have $python_version)"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Local Development Environment Variables
ENVIRONMENT=development
PROJECT_ID=california-motion-writer
REGION=us-central1

# Database (for local testing, use SQLite or local PostgreSQL)
DATABASE_URL=sqlite:///./test.db

# Mock secrets for local development
SECRET_KEY=local-development-secret-key-change-in-production
DB_PASSWORD_SECRET=local-password

# API Settings
API_V1_PREFIX=/api/v1
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Pub/Sub
PUBSUB_TOPIC=app-events

# Storage
GCS_BUCKET=california-motion-writer-documents

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash

# Vector Search
INDEX_ID=8771272646722584576
INDEX_ENDPOINT_ID=1505347966657888256
EOF
    echo "✅ Created .env file with default values"
    echo "⚠️  Please update with your actual GCP credentials if needed"
fi

# Check if forms directory exists
if [ ! -d "forms" ]; then
    mkdir -p forms
    echo "📁 Created forms/ directory"
    echo "⚠️  Remember to download official CA court forms and place them in forms/"
fi

# Run database migrations (if using local PostgreSQL)
# echo "🗄️ Running database migrations..."
# alembic upgrade head

# Start the application
echo ""
echo "🎯 Starting FastAPI application..."
echo "======================================================="
echo "📍 Local URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================="

# Run with auto-reload for development (frontend/.env points at port 8000)
USE_GCP=false uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload