#!/bin/bash

# ✈️ Airline Elite - Perfect Installation Script

echo "✨ Starting Perfect Installation for Airline Elite AI Agent..."

# 1. Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📦 Installing premium dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup Environment Variables
if [ ! -f .env ]; then
    echo "🔑 No .env found. Creating from example..."
    cp .env.example .env
    echo "⚠️  ACTION REQUIRED: Please open .env and add your API keys."
else
    echo "✅ .env file already exists."
fi

echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "------------------------------------------------"
echo "To start your AI Agent:"
echo "1. source venv/bin/activate"
echo "2. python server.py"
echo "3. Visit http://localhost:8000 in your browser"
echo "------------------------------------------------"
