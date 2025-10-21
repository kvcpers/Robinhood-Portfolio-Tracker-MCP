#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Adapter for Robinhood Portfolio Tracker
Enables AI models to interact with your trading system through a standardized interface.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import subprocess
import requests
from datetime import datetime

# Add the robinhood_tracker module to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Note: The MCP adapter uses HTTP requests to communicate with the API server
# rather than importing the robinhood_tracker modules directly
# This allows it to work independently of the Python environment

@dataclass
class MCPResponse:
    """Standard MCP response format"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class RobinhoodMCPAdapter:
    """MCP Adapter for Robinhood Portfolio Tracker"""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:5000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
    async def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> MCPResponse:
        """Make HTTP request to the Robinhood API server"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                return MCPResponse(success=False, error=f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            return MCPResponse(
                success=result.get("success", True),
                data=result.get("data"),
                error=result.get("error")
            )
            
        except requests.exceptions.RequestException as e:
            return MCPResponse(success=False, error=f"API request failed: {str(e)}")
        except Exception as e:
            return MCPResponse(success=False, error=f"Unexpected error: {str(e)}")

    # Portfolio Management Tools
    async def get_portfolio(self) -> MCPResponse:
        """Get current portfolio summary"""
        return await self._make_request("/api/portfolio")
    
    async def get_health(self) -> MCPResponse:
        """Check API server health"""
        return await self._make_request("/api/health")
    
    async def login(self) -> MCPResponse:
        """Login to Robinhood"""
        return await self._make_request("/api/login", "POST")
    
    # Trading Tools
    async def buy_stock(self, symbol: str, quantity: float) -> MCPResponse:
        """Buy stock shares"""
        data = {"symbol": symbol, "quantity": quantity}
        return await self._make_request("/api/buy", "POST", data)
    
    async def sell_stock(self, symbol: str, quantity: float) -> MCPResponse:
        """Sell stock shares"""
        data = {"symbol": symbol, "quantity": quantity}
        return await self._make_request("/api/sell", "POST", data)
    
    async def rebalance_portfolio(self, symbols: List[str], allocations: List[float], cash_buffer: float = 2.0) -> MCPResponse:
        """Rebalance portfolio according to target allocations"""
        data = {
            "symbols": symbols,
            "allocations": allocations,
            "cash_buffer": cash_buffer
        }
        return await self._make_request("/api/rebalance", "POST", data)
    
    # Trading Bot Tools
    async def get_bot_status(self) -> MCPResponse:
        """Get trading bot status and positions"""
        return await self._make_request("/api/bot/status")
    
    async def add_bot_position(self, symbol: str, quantity: float, stop_loss: float, take_profit: float) -> MCPResponse:
        """Add position to trading bot monitoring"""
        data = {
            "symbol": symbol,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
        return await self._make_request("/api/bot/add", "POST", data)
    
    async def remove_bot_position(self, symbol: str) -> MCPResponse:
        """Remove position from trading bot monitoring"""
        data = {"symbol": symbol}
        return await self._make_request("/api/bot/remove", "POST", data)
    
    async def start_bot(self, interval_minutes: int = 5) -> MCPResponse:
        """Start the trading bot"""
        data = {"interval": interval_minutes}
        return await self._make_request("/api/bot/start", "POST", data)
    
    async def stop_bot(self) -> MCPResponse:
        """Stop the trading bot"""
        return await self._make_request("/api/bot/stop", "POST")
    
    async def check_bot_positions(self) -> MCPResponse:
        """Manually check all bot positions"""
        return await self._make_request("/api/bot/check", "POST")
    
    # Options Tools
    async def get_options_positions(self) -> MCPResponse:
        """Get current options positions"""
        return await self._make_request("/api/options/positions")
    
    async def get_options_orders(self) -> MCPResponse:
        """Get recent options orders"""
        return await self._make_request("/api/options/orders")
    
    async def get_options_instruments(self, symbol: str) -> MCPResponse:
        """Get available options for a symbol"""
        return await self._make_request(f"/api/options/instruments/{symbol}")

class MCPToolRegistry:
    """Registry of available MCP tools for AI models"""
    
    def __init__(self, adapter: RobinhoodMCPAdapter):
        self.adapter = adapter
        self.tools = {
            # Portfolio Management
            "get_portfolio": {
                "description": "Get current portfolio summary including positions, cash, and total value",
                "parameters": {},
                "handler": adapter.get_portfolio
            },
            "get_health": {
                "description": "Check if the Robinhood API server is running and healthy",
                "parameters": {},
                "handler": adapter.get_health
            },
            "login": {
                "description": "Login to Robinhood account",
                "parameters": {},
                "handler": adapter.login
            },
            
            # Trading Operations
            "buy_stock": {
                "description": "Buy shares of a stock",
                "parameters": {
                    "symbol": {"type": "string", "description": "Stock symbol (e.g., AAPL, TSLA)"},
                    "quantity": {"type": "number", "description": "Number of shares to buy"}
                },
                "handler": adapter.buy_stock
            },
            "sell_stock": {
                "description": "Sell shares of a stock",
                "parameters": {
                    "symbol": {"type": "string", "description": "Stock symbol (e.g., AAPL, TSLA)"},
                    "quantity": {"type": "number", "description": "Number of shares to sell"}
                },
                "handler": adapter.sell_stock
            },
            "rebalance_portfolio": {
                "description": "Rebalance portfolio according to target allocations",
                "parameters": {
                    "symbols": {"type": "array", "description": "List of stock symbols"},
                    "allocations": {"type": "array", "description": "Target allocation percentages"},
                    "cash_buffer": {"type": "number", "description": "Cash buffer percentage", "default": 2.0}
                },
                "handler": adapter.rebalance_portfolio
            },
            
            # Trading Bot Management
            "get_bot_status": {
                "description": "Get trading bot status and monitored positions",
                "parameters": {},
                "handler": adapter.get_bot_status
            },
            "add_bot_position": {
                "description": "Add a position to trading bot monitoring with stop-loss and take-profit",
                "parameters": {
                    "symbol": {"type": "string", "description": "Stock symbol to monitor"},
                    "quantity": {"type": "number", "description": "Number of shares"},
                    "stop_loss": {"type": "number", "description": "Stop loss percentage (e.g., 5 for 5% loss)"},
                    "take_profit": {"type": "number", "description": "Take profit percentage (e.g., 10 for 10% gain)"}
                },
                "handler": adapter.add_bot_position
            },
            "remove_bot_position": {
                "description": "Remove a position from trading bot monitoring",
                "parameters": {
                    "symbol": {"type": "string", "description": "Stock symbol to remove from monitoring"}
                },
                "handler": adapter.remove_bot_position
            },
            "start_bot": {
                "description": "Start the automated trading bot",
                "parameters": {
                    "interval_minutes": {"type": "number", "description": "Check interval in minutes", "default": 5}
                },
                "handler": adapter.start_bot
            },
            "stop_bot": {
                "description": "Stop the automated trading bot",
                "parameters": {},
                "handler": adapter.stop_bot
            },
            "check_bot_positions": {
                "description": "Manually check all bot positions for stop-loss/take-profit triggers",
                "parameters": {},
                "handler": adapter.check_bot_positions
            },
            
            # Options Management
            "get_options_positions": {
                "description": "Get current options positions",
                "parameters": {},
                "handler": adapter.get_options_positions
            },
            "get_options_orders": {
                "description": "Get recent options orders",
                "parameters": {},
                "handler": adapter.get_options_orders
            },
            "get_options_instruments": {
                "description": "Get available options contracts for a symbol",
                "parameters": {
                    "symbol": {"type": "string", "description": "Stock symbol to get options for"}
                },
                "handler": adapter.get_options_instruments
            }
        }
    
    def get_tool_schema(self, tool_name: str) -> Dict:
        """Get schema for a specific tool"""
        if tool_name not in self.tools:
            return None
        return self.tools[tool_name]
    
    def list_tools(self) -> Dict:
        """Get list of all available tools"""
        return {name: {
            "description": tool["description"],
            "parameters": tool["parameters"]
        } for name, tool in self.tools.items()}
    
    async def execute_tool(self, tool_name: str, parameters: Dict = None) -> MCPResponse:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")
        
        if parameters is None:
            parameters = {}
        
        try:
            handler = self.tools[tool_name]["handler"]
            return await handler(**parameters)
        except Exception as e:
            return MCPResponse(success=False, error=f"Tool execution failed: {str(e)}")

# CLI Interface for testing
async def main():
    """CLI interface for testing the MCP adapter"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robinhood MCP Adapter CLI")
    parser.add_argument("--api-url", default="http://127.0.0.1:5000", help="API server URL")
    parser.add_argument("--tool", help="Tool to execute")
    parser.add_argument("--params", help="JSON parameters for the tool")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    
    args = parser.parse_args()
    
    adapter = RobinhoodMCPAdapter(args.api_url)
    registry = MCPToolRegistry(adapter)
    
    if args.list_tools:
        tools = registry.list_tools()
        print("Available MCP Tools:")
        print(json.dumps(tools, indent=2))
        return
    
    if args.tool:
        params = json.loads(args.params) if args.params else {}
        result = await registry.execute_tool(args.tool, params)
        print(json.dumps({
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "timestamp": result.timestamp
        }, indent=2))
    else:
        # Interactive mode
        print("Robinhood MCP Adapter - Interactive Mode")
        print("Type 'help' for available commands, 'exit' to quit")
        
        while True:
            try:
                command = input("\nMCP> ").strip()
                
                if command == "exit":
                    break
                elif command == "help":
                    tools = registry.list_tools()
                    print("\nAvailable tools:")
                    for name, tool in tools.items():
                        print(f"  {name}: {tool['description']}")
                elif command.startswith("list"):
                    tools = registry.list_tools()
                    print(json.dumps(tools, indent=2))
                elif command.startswith("exec "):
                    parts = command.split(" ", 2)
                    if len(parts) >= 2:
                        tool_name = parts[1]
                        params_str = parts[2] if len(parts) > 2 else "{}"
                        params = json.loads(params_str)
                        
                        result = await registry.execute_tool(tool_name, params)
                        print(json.dumps({
                            "success": result.success,
                            "data": result.data,
                            "error": result.error,
                            "timestamp": result.timestamp
                        }, indent=2))
                    else:
                        print("Usage: exec <tool_name> [json_parameters]")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
