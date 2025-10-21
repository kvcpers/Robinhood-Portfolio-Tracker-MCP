#!/usr/bin/env python3
"""
MCP Server for Robinhood Portfolio Tracker
Provides a standardized interface for AI models to interact with your trading system.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
import argparse
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_robinhood_adapter import RobinhoodMCPAdapter, MCPToolRegistry, MCPResponse

class MCPServer:
    """MCP Server implementation for Robinhood integration"""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:5000"):
        self.adapter = RobinhoodMCPAdapter(api_base_url)
        self.registry = MCPToolRegistry(self.adapter)
        self.session_id = f"robinhood_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming MCP requests"""
        try:
            # Handle both MCP protocol and direct method calls
            method = request.get("method", "")
            request_type = request.get("type", "")
            request_id = request.get("id", "unknown")
            
            # Handle MCP protocol requests
            if method == "tools/list":
                return await self._handle_list_tools(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request_id, request.get("params", {}))
            elif method == "initialize":
                return await self._handle_initialize(request_id, request.get("params", {}))
            # Handle direct type-based requests
            elif request_type == "tools/list":
                return await self._handle_list_tools(request_id)
            elif request_type == "tools/call":
                return await self._handle_tool_call(request_id, request.get("params", {}))
            elif request_type == "initialize":
                return await self._handle_initialize(request_id, request.get("params", {}))
            else:
                return self._error_response(request_id, f"Unknown request type/method: {request_type or method}")
                
        except Exception as e:
            return self._error_response(request.get("id", "unknown"), f"Server error: {str(e)}")
    
    async def _handle_initialize(self, request_id: str, params: Dict) -> Dict:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "robinhood-mcp-server",
                    "version": "1.0.0",
                    "description": "MCP server for Robinhood Portfolio Tracker"
                }
            }
        }
    
    async def _handle_list_tools(self, request_id: str) -> Dict:
        """Handle tools list request"""
        tools = self.registry.list_tools()
        tool_list = []
        
        for name, tool_info in tools.items():
            tool_list.append({
                "name": name,
                "description": tool_info["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": tool_info["parameters"],
                    "required": [key for key, value in tool_info["parameters"].items() 
                               if "default" not in value]
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tool_list
            }
        }
    
    async def _handle_tool_call(self, request_id: str, params: Dict) -> Dict:
        """Handle tool execution request"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._error_response(request_id, "Tool name is required")
        
        # Execute the tool
        result = await self.registry.execute_tool(tool_name, arguments)
        
        # Format the response
        if result.success:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.data, indent=2) if result.data else "Success"
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": result.error or "Tool execution failed"
                }
            }
    
    def _error_response(self, request_id: str, message: str) -> Dict:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": message
            }
        }

class MCPClient:
    """Simple MCP client for testing the server"""
    
    def __init__(self, server: MCPServer):
        self.server = server
    
    async def send_request(self, request: Dict) -> Dict:
        """Send request to MCP server"""
        return await self.server.handle_request(request)
    
    async def list_tools(self) -> Dict:
        """List available tools"""
        request = {
            "jsonrpc": "2.0",
            "id": "list_tools",
            "method": "tools/list"
        }
        return await self.send_request(request)
    
    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """Call a specific tool"""
        if arguments is None:
            arguments = {}
        
        request = {
            "jsonrpc": "2.0",
            "id": f"call_{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return await self.send_request(request)

async def test_server():
    """Test the MCP server functionality"""
    print("🧪 Testing Robinhood MCP Server")
    print("=" * 50)
    
    # Initialize server
    server = MCPServer()
    client = MCPClient(server)
    
    # Test 1: List tools
    print("\n1. Listing available tools...")
    tools_response = await client.list_tools()
    if "result" in tools_response:
        tools = tools_response["result"]["tools"]
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    else:
        print(f"❌ Error listing tools: {tools_response}")
    
    # Test 2: Check health
    print("\n2. Checking API health...")
    health_response = await client.call_tool("get_health")
    if "result" in health_response:
        print("✅ API server is healthy")
    else:
        print(f"❌ Health check failed: {health_response}")
    
    # Test 3: Get portfolio
    print("\n3. Getting portfolio...")
    portfolio_response = await client.call_tool("get_portfolio")
    if "result" in portfolio_response:
        print("✅ Portfolio data retrieved successfully")
        # Print a summary
        content = portfolio_response["result"]["content"][0]["text"]
        portfolio_data = json.loads(content)
        if portfolio_data and "data" in portfolio_data:
            data = portfolio_data["data"]
            print(f"   Total Value: ${data.get('total_value', 'N/A')}")
            print(f"   Cash: ${data.get('cash', 'N/A')}")
            print(f"   Positions: {len(data.get('positions', []))}")
    else:
        print(f"❌ Portfolio retrieval failed: {portfolio_response}")
    
    # Test 4: Get bot status
    print("\n4. Getting bot status...")
    bot_response = await client.call_tool("get_bot_status")
    if "result" in bot_response:
        print("✅ Bot status retrieved successfully")
    else:
        print(f"❌ Bot status retrieval failed: {bot_response}")
    
    print("\n🎉 MCP Server testing completed!")

async def interactive_mode():
    """Interactive mode for manual testing"""
    print("🤖 Robinhood MCP Server - Interactive Mode")
    print("=" * 50)
    print("Available commands:")
    print("  list - List available tools")
    print("  call <tool_name> [args] - Call a tool")
    print("  health - Check API health")
    print("  portfolio - Get portfolio")
    print("  bot - Get bot status")
    print("  exit - Exit")
    
    server = MCPServer()
    client = MCPClient(server)
    
    while True:
        try:
            command = input("\nMCP> ").strip()
            
            if command == "exit":
                break
            elif command == "list":
                response = await client.list_tools()
                if "result" in response:
                    tools = response["result"]["tools"]
                    print(f"\nAvailable tools ({len(tools)}):")
                    for tool in tools:
                        print(f"  {tool['name']}: {tool['description']}")
                else:
                    print(f"Error: {response}")
            elif command == "health":
                response = await client.call_tool("get_health")
                print(json.dumps(response, indent=2))
            elif command == "portfolio":
                response = await client.call_tool("get_portfolio")
                print(json.dumps(response, indent=2))
            elif command == "bot":
                response = await client.call_tool("get_bot_status")
                print(json.dumps(response, indent=2))
            elif command.startswith("call "):
                parts = command.split(" ", 2)
                if len(parts) >= 2:
                    tool_name = parts[1]
                    args_str = parts[2] if len(parts) > 2 else "{}"
                    try:
                        args = json.loads(args_str)
                        response = await client.call_tool(tool_name, args)
                        print(json.dumps(response, indent=2))
                    except json.JSONDecodeError:
                        print("Invalid JSON in arguments")
                else:
                    print("Usage: call <tool_name> [json_arguments]")
            else:
                print("Unknown command. Type 'list' to see available tools.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Robinhood MCP Server")
    parser.add_argument("--api-url", default="http://127.0.0.1:5000", 
                       help="Robinhood API server URL")
    parser.add_argument("--test", action="store_true", 
                       help="Run server tests")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_server())
    elif args.interactive:
        asyncio.run(interactive_mode())
    else:
        print("Robinhood MCP Server")
        print("Use --test to run tests or --interactive for manual testing")
        print("Make sure your Robinhood API server is running on", args.api_url)

if __name__ == "__main__":
    main()
