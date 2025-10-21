#!/usr/bin/env python3
"""
Example usage of the Robinhood MCP Adapter
Demonstrates common trading operations through the MCP interface.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_robinhood_adapter import RobinhoodMCPAdapter, MCPToolRegistry

async def example_portfolio_management():
    """Example: Basic portfolio management operations"""
    print("📊 Portfolio Management Example")
    print("=" * 40)
    
    adapter = RobinhoodMCPAdapter()
    
    # 1. Check API health
    print("1. Checking API health...")
    health = await adapter.get_health()
    if health.success:
        print("✅ API server is healthy")
    else:
        print(f"❌ API health check failed: {health.error}")
        return
    
    # 2. Get portfolio summary
    print("\n2. Getting portfolio summary...")
    portfolio = await adapter.get_portfolio()
    if portfolio.success and portfolio.data:
        data = portfolio.data
        print(f"✅ Portfolio retrieved successfully")
        print(f"   Total Value: ${data.get('total_value', 'N/A')}")
        print(f"   Cash: ${data.get('cash', 'N/A')}")
        print(f"   Positions: {len(data.get('positions', []))}")
        
        # Show top positions
        positions = data.get('positions', [])
        if positions:
            print(f"\n   Top Positions:")
            for i, pos in enumerate(positions[:3]):  # Show top 3
                symbol = pos.get('symbol', 'N/A')
                value = pos.get('market_value', 0)
                print(f"   {i+1}. {symbol}: ${value:.2f}")
    else:
        print(f"❌ Failed to get portfolio: {portfolio.error}")

async def example_trading_operations():
    """Example: Trading operations (PAPER TRADING ONLY)"""
    print("\n💰 Trading Operations Example")
    print("=" * 40)
    print("⚠️  This example uses PAPER TRADING - no real money involved!")
    
    adapter = RobinhoodMCPAdapter()
    
    # 1. Buy a small amount of stock (paper trading)
    print("\n1. Buying 1 share of AAPL (paper trading)...")
    buy_result = await adapter.buy_stock("AAPL", 1)
    if buy_result.success:
        print("✅ Buy order placed successfully")
        print(f"   Response: {buy_result.data}")
    else:
        print(f"❌ Buy order failed: {buy_result.error}")
    
    # 2. Check portfolio after purchase
    print("\n2. Checking portfolio after purchase...")
    portfolio = await adapter.get_portfolio()
    if portfolio.success:
        print("✅ Portfolio updated")
    else:
        print(f"❌ Failed to get updated portfolio: {portfolio.error}")

async def example_trading_bot():
    """Example: Trading bot management"""
    print("\n🤖 Trading Bot Example")
    print("=" * 40)
    
    adapter = RobinhoodMCPAdapter()
    
    # 1. Get current bot status
    print("1. Getting bot status...")
    bot_status = await adapter.get_bot_status()
    if bot_status.success:
        print("✅ Bot status retrieved")
        data = bot_status.data
        print(f"   Running: {data.get('running', False)}")
        print(f"   Positions monitored: {len(data.get('positions', []))}")
        
        # Show monitored positions
        positions = data.get('positions', [])
        if positions:
            print(f"\n   Monitored Positions:")
            for pos in positions:
                symbol = pos.get('symbol', 'N/A')
                quantity = pos.get('quantity', 0)
                stop_loss = pos.get('stop_loss_pct', 0)
                take_profit = pos.get('take_profit_pct', 0)
                print(f"   - {symbol}: {quantity} shares, SL: {stop_loss}%, TP: {take_profit}%")
    else:
        print(f"❌ Failed to get bot status: {bot_status.error}")
    
    # 2. Add a position to monitoring (example)
    print("\n2. Adding position to bot monitoring...")
    add_result = await adapter.add_bot_position("AAPL", 1, 5, 10)  # 5% stop loss, 10% take profit
    if add_result.success:
        print("✅ Position added to monitoring")
    else:
        print(f"❌ Failed to add position: {add_result.error}")
    
    # 3. Start the bot
    print("\n3. Starting the trading bot...")
    start_result = await adapter.start_bot(5)  # 5-minute intervals
    if start_result.success:
        print("✅ Trading bot started")
    else:
        print(f"❌ Failed to start bot: {start_result.error}")

async def example_options_trading():
    """Example: Options trading operations"""
    print("\n📈 Options Trading Example")
    print("=" * 40)
    
    adapter = RobinhoodMCPAdapter()
    
    # 1. Get options positions
    print("1. Getting options positions...")
    options_positions = await adapter.get_options_positions()
    if options_positions.success:
        print("✅ Options positions retrieved")
        data = options_positions.data
        if data and 'results' in data:
            positions = data['results']
            active_positions = [p for p in positions if float(p.get('quantity', 0)) > 0]
            print(f"   Active options positions: {len(active_positions)}")
            
            if active_positions:
                for pos in active_positions[:3]:  # Show first 3
                    symbol = pos.get('chain_symbol', 'N/A')
                    quantity = pos.get('quantity', 0)
                    option_type = pos.get('type', 'N/A')
                    print(f"   - {symbol} {option_type}: {quantity} contracts")
            else:
                print("   No active options positions")
        else:
            print("   No options data available")
    else:
        print(f"❌ Failed to get options positions: {options_positions.error}")
    
    # 2. Get options for a specific symbol
    print("\n2. Getting options instruments for AAPL...")
    options_instruments = await adapter.get_options_instruments("AAPL")
    if options_instruments.success:
        print("✅ Options instruments retrieved")
        data = options_instruments.data
        if data and 'results' in data:
            instruments = data['results']
            print(f"   Available options contracts: {len(instruments)}")
        else:
            print("   No options instruments available")
    else:
        print(f"❌ Failed to get options instruments: {options_instruments.error}")

async def example_portfolio_rebalancing():
    """Example: Portfolio rebalancing"""
    print("\n⚖️ Portfolio Rebalancing Example")
    print("=" * 40)
    
    adapter = RobinhoodMCPAdapter()
    
    # Example rebalancing: 60% AAPL, 30% TSLA, 10% cash
    print("1. Rebalancing portfolio...")
    print("   Target allocation: 60% AAPL, 30% TSLA, 10% cash")
    
    rebalance_result = await adapter.rebalance_portfolio(
        symbols=["AAPL", "TSLA"],
        allocations=[0.6, 0.3],
        cash_buffer=0.1
    )
    
    if rebalance_result.success:
        print("✅ Portfolio rebalancing completed")
        print(f"   Response: {rebalance_result.data}")
    else:
        print(f"❌ Rebalancing failed: {rebalance_result.error}")

async def interactive_demo():
    """Interactive demonstration of MCP tools"""
    print("\n🎮 Interactive MCP Demo")
    print("=" * 40)
    print("Available commands:")
    print("  portfolio - Get portfolio summary")
    print("  bot - Get bot status")
    print("  options - Get options positions")
    print("  health - Check API health")
    print("  exit - Exit demo")
    
    adapter = RobinhoodMCPAdapter()
    
    while True:
        try:
            command = input("\nDemo> ").strip().lower()
            
            if command == "exit":
                break
            elif command == "portfolio":
                result = await adapter.get_portfolio()
                print(json.dumps(result.data, indent=2) if result.success else result.error)
            elif command == "bot":
                result = await adapter.get_bot_status()
                print(json.dumps(result.data, indent=2) if result.success else result.error)
            elif command == "options":
                result = await adapter.get_options_positions()
                print(json.dumps(result.data, indent=2) if result.success else result.error)
            elif command == "health":
                result = await adapter.get_health()
                print("✅ Healthy" if result.success else f"❌ {result.error}")
            else:
                print("Unknown command. Type 'exit' to quit.")
                
        except KeyboardInterrupt:
            print("\nExiting demo...")
            break
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main example function"""
    print("🚀 Robinhood MCP Adapter Examples")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  Make sure your Robinhood API server is running on http://127.0.0.1:5000")
    
    try:
        # Run examples
        await example_portfolio_management()
        await example_trading_operations()
        await example_trading_bot()
        await example_options_trading()
        await example_portfolio_rebalancing()
        
        # Interactive demo
        print("\n" + "=" * 50)
        await interactive_demo()
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("Make sure your Robinhood API server is running!")

if __name__ == "__main__":
    asyncio.run(main())
