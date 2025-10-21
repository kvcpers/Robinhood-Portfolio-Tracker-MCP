# Robinhood MCP (Model Context Protocol) Adapter

This MCP adapter enables AI models to interact with your Robinhood Portfolio Tracker through a standardized interface. It allows AI assistants to execute trades, monitor your portfolio, and manage your automated trading bot.

## 🚀 Features

### Portfolio Management
- **Get Portfolio**: Retrieve current portfolio summary, positions, and cash balance
- **Health Check**: Verify API server status
- **Login**: Authenticate with Robinhood

### Trading Operations
- **Buy/Sell Stocks**: Execute stock trades with specified quantities
- **Portfolio Rebalancing**: Automatically rebalance portfolio according to target allocations

### Trading Bot Management
- **Monitor Positions**: Add positions to automated monitoring
- **Stop Loss/Take Profit**: Set automated triggers for position management
- **Bot Control**: Start/stop the automated trading bot
- **Status Monitoring**: Check bot status and monitored positions

### Options Trading
- **Options Positions**: View current options holdings
- **Options Orders**: Check recent options transactions
- **Options Instruments**: Get available options contracts for symbols

## 📋 Prerequisites

1. **Running Robinhood API Server**: Your Flask API server must be running on `http://127.0.0.1:5000`
2. **Python Dependencies**: Install required packages
3. **Authentication**: Ensure your Robinhood credentials are configured

## 🛠️ Installation

1. **Make the scripts executable**:
   ```bash
   chmod +x mcp_robinhood_adapter.py
   chmod +x mcp_server.py
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   pip install requests asyncio
   ```

## 🎯 Usage

### 1. Basic CLI Usage

```bash
# List available tools
python mcp_robinhood_adapter.py --list-tools

# Execute a specific tool
python mcp_robinhood_adapter.py --tool get_portfolio

# Execute tool with parameters
python mcp_robinhood_adapter.py --tool buy_stock --params '{"symbol": "AAPL", "quantity": 1}'
```

### 2. Interactive Mode

```bash
# Start interactive mode
python mcp_robinhood_adapter.py

# Available commands:
# - help: Show available tools
# - exec <tool_name> [params]: Execute a tool
# - list: List all tools
# - exit: Quit
```

### 3. MCP Server Testing

```bash
# Run server tests
python mcp_server.py --test

# Interactive server mode
python mcp_server.py --interactive
```

## 🔧 Available Tools

### Portfolio Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_portfolio` | Get portfolio summary | None |
| `get_health` | Check API health | None |
| `login` | Login to Robinhood | None |

### Trading Operations
| Tool | Description | Parameters |
|------|-------------|------------|
| `buy_stock` | Buy stock shares | `symbol`, `quantity` |
| `sell_stock` | Sell stock shares | `symbol`, `quantity` |
| `rebalance_portfolio` | Rebalance portfolio | `symbols`, `allocations`, `cash_buffer` |

### Trading Bot Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_bot_status` | Get bot status | None |
| `add_bot_position` | Add position to monitoring | `symbol`, `quantity`, `stop_loss`, `take_profit` |
| `remove_bot_position` | Remove position from monitoring | `symbol` |
| `start_bot` | Start automated bot | `interval_minutes` |
| `stop_bot` | Stop automated bot | None |
| `check_bot_positions` | Check all positions | None |

### Options Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_options_positions` | Get options positions | None |
| `get_options_orders` | Get options orders | None |
| `get_options_instruments` | Get options for symbol | `symbol` |

## 📝 Example Usage

### Example 1: Check Portfolio and Buy Stock

```python
import asyncio
from mcp_robinhood_adapter import RobinhoodMCPAdapter

async def example():
    adapter = RobinhoodMCPAdapter()
    
    # Check portfolio
    portfolio = await adapter.get_portfolio()
    print(f"Portfolio value: ${portfolio.data['total_value']}")
    
    # Buy 1 share of AAPL
    buy_result = await adapter.buy_stock("AAPL", 1)
    print(f"Buy result: {buy_result.success}")

asyncio.run(example())
```

### Example 2: Set Up Automated Trading

```python
async def setup_automated_trading():
    adapter = RobinhoodMCPAdapter()
    
    # Add AAPL position with 5% stop loss and 10% take profit
    await adapter.add_bot_position("AAPL", 10, 5, 10)
    
    # Start the bot with 5-minute intervals
    await adapter.start_bot(5)
    
    # Check bot status
    status = await adapter.get_bot_status()
    print(f"Bot running: {status.data['running']}")
```

### Example 3: Portfolio Rebalancing

```python
async def rebalance_example():
    adapter = RobinhoodMCPAdapter()
    
    # Rebalance to 60% AAPL, 30% TSLA, 10% cash
    await adapter.rebalance_portfolio(
        symbols=["AAPL", "TSLA"],
        allocations=[0.6, 0.3],
        cash_buffer=0.1
    )
```

## 🔌 Integration with AI Models

### Claude Desktop Integration

To use with Claude Desktop, create a configuration file:

```json
{
  "mcpServers": {
    "robinhood": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "API_URL": "http://127.0.0.1:5000"
      }
    }
  }
}
```

### OpenAI Function Calling

```python
# Example OpenAI function calling integration
functions = [
    {
        "name": "get_portfolio",
        "description": "Get current portfolio summary",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "buy_stock",
        "description": "Buy shares of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "quantity": {"type": "number", "description": "Number of shares"}
            },
            "required": ["symbol", "quantity"]
        }
    }
]
```

## 🛡️ Security Considerations

1. **API Server**: Ensure your Robinhood API server is running locally and not exposed to the internet
2. **Credentials**: Keep your Robinhood credentials secure and use environment variables
3. **Paper Trading**: Use paper trading mode (`RH_PAPER=true`) for testing
4. **Rate Limiting**: Be mindful of API rate limits when using automated tools

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure your Robinhood API server is running on port 5000
2. **Authentication Errors**: Verify your Robinhood credentials are correct
3. **Tool Execution Failures**: Check that the API server is healthy with `get_health`

### Debug Mode

```bash
# Enable debug logging
export DEBUG=1
python mcp_server.py --interactive
```

## 📊 Response Format

All MCP responses follow this format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This MCP adapter is part of the Robinhood Portfolio Tracker project and follows the same license terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API server logs
3. Ensure all dependencies are installed
4. Verify your Robinhood API server is running

---

**⚠️ Important**: This adapter provides programmatic access to your trading account. Use with caution and always test with paper trading first!
