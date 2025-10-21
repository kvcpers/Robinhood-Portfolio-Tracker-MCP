#!/usr/bin/env python3
"""
Test script for the Robinhood MCP Adapter
Verifies that all components are working correctly.
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp_robinhood_adapter import RobinhoodMCPAdapter, MCPToolRegistry
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory with all MCP files")
    sys.exit(1)

async def test_api_connection():
    """Test connection to the Robinhood API server"""
    print("🔌 Testing API Connection")
    print("-" * 30)
    
    try:
        # Test direct HTTP connection
        response = requests.get("http://127.0.0.1:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is responding")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure your Robinhood API server is running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def test_mcp_adapter():
    """Test the MCP adapter functionality"""
    print("\n🔧 Testing MCP Adapter")
    print("-" * 30)
    
    adapter = RobinhoodMCPAdapter()
    
    # Test 1: Health check
    print("1. Testing health check...")
    health = await adapter.get_health()
    if health.success:
        print("   ✅ Health check passed")
    else:
        print(f"   ❌ Health check failed: {health.error}")
        return False
    
    # Test 2: Portfolio retrieval
    print("2. Testing portfolio retrieval...")
    portfolio = await adapter.get_portfolio()
    if portfolio.success:
        print("   ✅ Portfolio retrieval passed")
        if portfolio.data:
            data = portfolio.data
            print(f"   📊 Total Value: ${data.get('total_value', 'N/A')}")
            print(f"   💰 Cash: ${data.get('cash', 'N/A')}")
            print(f"   📈 Positions: {len(data.get('positions', []))}")
    else:
        print(f"   ❌ Portfolio retrieval failed: {portfolio.error}")
        return False
    
    # Test 3: Bot status
    print("3. Testing bot status...")
    bot_status = await adapter.get_bot_status()
    if bot_status.success:
        print("   ✅ Bot status retrieval passed")
        if bot_status.data:
            data = bot_status.data
            print(f"   🤖 Bot running: {data.get('running', False)}")
            print(f"   📊 Monitored positions: {len(data.get('positions', []))}")
    else:
        print(f"   ❌ Bot status retrieval failed: {bot_status.error}")
        return False
    
    return True

async def test_tool_registry():
    """Test the MCP tool registry"""
    print("\n🛠️ Testing Tool Registry")
    print("-" * 30)
    
    adapter = RobinhoodMCPAdapter()
    registry = MCPToolRegistry(adapter)
    
    # Test 1: List tools
    print("1. Testing tool listing...")
    tools = registry.list_tools()
    print(f"   ✅ Found {len(tools)} tools")
    
    # Show some tools
    tool_names = list(tools.keys())[:5]  # Show first 5
    print(f"   📋 Sample tools: {', '.join(tool_names)}")
    
    # Test 2: Tool schema
    print("2. Testing tool schemas...")
    for tool_name in ["get_portfolio", "buy_stock", "get_bot_status"]:
        schema = registry.get_tool_schema(tool_name)
        if schema:
            print(f"   ✅ {tool_name}: {schema['description'][:50]}...")
        else:
            print(f"   ❌ {tool_name}: Schema not found")
    
    # Test 3: Tool execution
    print("3. Testing tool execution...")
    result = await registry.execute_tool("get_health")
    if result.success:
        print("   ✅ Tool execution test passed")
    else:
        print(f"   ❌ Tool execution test failed: {result.error}")
        return False
    
    return True

async def test_specific_tools():
    """Test specific MCP tools"""
    print("\n🎯 Testing Specific Tools")
    print("-" * 30)
    
    adapter = RobinhoodMCPAdapter()
    
    # Test tools that don't require parameters
    test_tools = [
        ("get_health", "Health check"),
        ("get_portfolio", "Portfolio summary"),
        ("get_bot_status", "Bot status"),
        ("get_options_positions", "Options positions")
    ]
    
    for tool_name, description in test_tools:
        print(f"Testing {tool_name} ({description})...")
        try:
            # Get the method from adapter
            method = getattr(adapter, tool_name)
            result = await method()
            
            if result.success:
                print(f"   ✅ {tool_name} passed")
            else:
                print(f"   ❌ {tool_name} failed: {result.error}")
        except Exception as e:
            print(f"   ❌ {tool_name} error: {e}")

def test_configuration():
    """Test configuration files"""
    print("\n📋 Testing Configuration")
    print("-" * 30)
    
    # Test MCP config file
    try:
        with open("mcp_config.json", "r") as f:
            config = json.load(f)
        print("✅ MCP configuration file is valid JSON")
        
        # Check required sections
        required_sections = ["mcpServers", "tools", "usage_examples"]
        for section in required_sections:
            if section in config:
                print(f"   ✅ {section} section present")
            else:
                print(f"   ❌ {section} section missing")
        
        # Count tools
        total_tools = 0
        for category, tools in config.get("tools", {}).items():
            total_tools += len(tools)
        print(f"   📊 Total tools configured: {total_tools}")
        
    except FileNotFoundError:
        print("❌ MCP configuration file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ MCP configuration file is invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True

async def run_all_tests():
    """Run all tests"""
    print("🧪 Robinhood MCP Adapter Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("API Connection", test_api_connection()),
        ("MCP Adapter", test_mcp_adapter()),
        ("Tool Registry", test_tool_registry()),
        ("Specific Tools", test_specific_tools()),
        ("Configuration", test_configuration())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your MCP adapter is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1)
