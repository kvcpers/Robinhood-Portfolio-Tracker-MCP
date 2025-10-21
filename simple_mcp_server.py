#!/usr/bin/env python3
"""
Simple MCP Server for Robinhood Portfolio Tracker
A lightweight server that can be used with AI models.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import requests

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_robinhood_adapter import RobinhoodMCPAdapter, MCPToolRegistry

class SimpleMCPServer:
    """Simple MCP server for AI model integration"""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:5000"):
        self.adapter = RobinhoodMCPAdapter(api_base_url)
        self.registry = MCPToolRegistry(self.adapter)
        self.running = True
    
    async def start_server(self):
        """Start the MCP server"""
        print("🚀 Starting Simple MCP Server for Robinhood")
        print("=" * 50)
        print("✅ MCP Server is running and ready for AI model integration")
        print("📊 Available tools: 15 trading and portfolio management tools")
        print("🔗 API Server: http://127.0.0.1:5000")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        # Test connection
        try:
            health = await self.adapter.get_health()
            if health.success:
                print("✅ Connected to Robinhood API server")
            else:
                print(f"⚠️  API server issue: {health.error}")
        except Exception as e:
            print(f"❌ Cannot connect to API server: {e}")
            print("Make sure your Robinhood API server is running!")
            return
        
        # Show available tools
        tools = self.registry.list_tools()
        print(f"🛠️  Available MCP Tools ({len(tools)}):")
        for name, tool in tools.items():
            print(f"   • {name}: {tool['description']}")
        
        print("\n🎯 MCP Server is ready for AI model integration!")
        print("Use this server with Claude Desktop or other AI tools.")
        
        # Keep server running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping MCP Server...")
            self.running = False
    
    def get_tools(self):
        """Get list of available tools"""
        return self.registry.list_tools()
    
    async def execute_tool(self, tool_name: str, parameters: dict = None):
        """Execute a tool"""
        if parameters is None:
            parameters = {}
        return await self.registry.execute_tool(tool_name, parameters)

async def main():
    """Main function"""
    server = SimpleMCPServer()
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
