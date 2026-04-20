#!/bin/bash
echo "🚀 Setting up SwiftShop Backend..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy env file if .env doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env file created from .env.example — please fill in your secrets!"
fi

echo ""
echo "✅ Setup complete! Run the server with:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "📚 API Docs: http://127.0.0.1:8000/docs"
