#!/bin/bash

echo "🚀 Setting up Humanoid Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your database credentials and Hugging Face API key!"
    read -p "Press Enter after you've edited the .env file..."
fi

# Create migrations directory if it doesn't exist
mkdir -p api/migrations
touch api/migrations/__init__.py

# Make migrations
echo "🗄️  Creating database migrations..."
python manage.py makemigrations

# Apply migrations
echo "🗄️  Applying database migrations..."
python manage.py migrate

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
