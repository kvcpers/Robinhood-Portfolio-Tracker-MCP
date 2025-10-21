#!/bin/bash
# Setup script for Robinhood MCP Adapter

echo "🚀 Setting up Robinhood MCP Adapter"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "mcp_robinhood_adapter.py" ]; then
    echo "❌ MCP adapter files not found. Make sure you're in the correct directory."
    exit 1
fi

echo "✅ Python 3 found"

# Make scripts executable
echo "📝 Making scripts executable..."
chmod +x mcp_robinhood_adapter.py
chmod +x mcp_server.py
chmod +x mcp_example.py
chmod +x test_mcp.py

echo "✅ Scripts made executable"

# Check if requests module is available
echo "🔍 Checking dependencies..."
python3 -c "import requests" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ requests module found"
else
    echo "⚠️  requests module not found. Installing..."
    pip3 install requests
fi

# Check if the Robinhood API server is running
echo "🔍 Checking Robinhood API server..."
curl -s http://127.0.0.1:5000/api/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Robinhood API server is running"
else
    echo "⚠️  Robinhood API server is not running"
    echo "   Start it with: source .venv/bin/activate && RH_PAPER=true python start_gui.py"
fi

echo ""
echo "🎉 MCP Adapter setup complete!"
echo ""
echo "📋 Available commands:"
echo "  ./test_mcp.py              - Run all tests"
echo "  ./mcp_example.py           - Run examples"
echo "  ./mcp_robinhood_adapter.py --list-tools - List available tools"
echo "  ./mcp_server.py --test     - Test MCP server"
echo "  ./mcp_server.py --interactive - Interactive mode"
echo ""
echo "📖 See MCP_README.md for detailed usage instructions"
