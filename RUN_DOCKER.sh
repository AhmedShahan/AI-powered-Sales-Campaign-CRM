#!/bin/bash
# Docker Compose Run Script

echo "🚀 Starting Sales Campaign CRM with Docker Compose..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your GOOGLE_API_KEY"
    echo "Example: echo 'GOOGLE_API_KEY=your_key_here' > .env"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=.*[^your_api_key_here]" .env 2>/dev/null; then
    echo "⚠️  Warning: Please make sure GOOGLE_API_KEY is set in .env file"
    echo ""
fi

# Run docker-compose
echo "📦 Building and starting containers..."
echo ""

# Try with sudo (if needed)
if sudo docker ps > /dev/null 2>&1; then
    echo "Using sudo for Docker commands..."
    sudo docker-compose up --build
else
    echo "Using regular Docker commands..."
    docker-compose up --build
fi

