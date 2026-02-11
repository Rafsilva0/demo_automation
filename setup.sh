#!/bin/bash
# Ada Agent Provisioning - Setup Script

set -e

echo "======================================"
echo "Ada Agent Provisioning - Setup"
echo "======================================"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "   ✓ Python $PYTHON_VERSION found"
else
    echo "   ❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if pip is available
echo ""
echo "📦 Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "   ✓ pip3 found"
else
    echo "   ❌ pip3 not found. Please install pip"
    exit 1
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo "   ✓ Dependencies installed"

# Install Playwright browsers
echo ""
echo "🎭 Installing Playwright browsers..."
if python3 -c "import playwright" 2>/dev/null; then
    playwright install chromium
    echo "   ✓ Playwright browsers installed"
else
    echo "   ⚠️  Playwright not in requirements.txt, skipping browser install"
fi

# Check for .env file
echo ""
echo "🔐 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"

    # Check for required keys
    if grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
        echo "   ✓ ANTHROPIC_API_KEY is set"
    else
        echo "   ⚠️  ANTHROPIC_API_KEY not set in .env"
        echo "      Add it to .env: ANTHROPIC_API_KEY=your_key_here"
    fi

    if grep -q "BEECEPTOR_AUTH_TOKEN=" .env; then
        echo "   ✓ BEECEPTOR_AUTH_TOKEN is set"
    else
        echo "   ⚠️  BEECEPTOR_AUTH_TOKEN not set in .env"
    fi
else
    echo "   ⚠️  .env file not found"
    echo "   Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✓ .env created - please edit it with your API keys"
    else
        echo "   ❌ .env.example not found"
    fi
fi

# Test Anthropic API key
echo ""
echo "🧪 Testing Anthropic API connection..."
export $(grep ANTHROPIC_API_KEY .env | xargs)

python3 << 'EOFPYTHON'
import os
import sys

try:
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "sk-your_key_here" or not api_key.startswith("sk-ant-"):
        print("   ⚠️  ANTHROPIC_API_KEY not properly configured")
        print("      Set it in .env file")
        sys.exit(0)

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print(f"   ✓ Anthropic API key is valid")
except Exception as e:
    print(f"   ❌ Anthropic API test failed: {e}")
EOFPYTHON

# Summary
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run a test: python3 provision.py --company \"Test Co\" --ada-key \"test\" --dry-run"
echo "  3. Run for real: python3 provision.py --company \"Pepsi\" --ada-key \"your_ada_key\""
echo ""
echo "For help: python3 provision.py --help"
echo ""
