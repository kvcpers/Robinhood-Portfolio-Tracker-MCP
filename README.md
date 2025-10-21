## Robinhood Portfolio Tracker (CLI)

This project provides a command-line portfolio tracker for Robinhood with login, portfolio viewing, and basic trading. It also includes a paper-trading mode for safe testing.

Important: Real-money trading is risky. Use paper mode first. You are responsible for your account and regulatory compliance.

### Features
- Login using username/password or device token with session caching
- View portfolio positions, cash, performance snapshot
- Place market buy/sell orders (limit support planned)
- Paper-trading mode with local state file
- Simple momentum strategy example and rebalance command

### Quick Start

1) Create and activate a virtual environment
```bash
python3 -m venv .venv && source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Set environment variables
```bash
export RH_USERNAME="your_email@example.com"
export RH_PASSWORD="your_password"
export RH_DEVICE_TOKEN="your_device_token_optional"
export RH_PAPER="true"  # set to "false" to enable live trading
# Optional: if you already have an access token from the web app
export RH_ACCESS_TOKEN="paste_access_token_here"
export RH_TOKEN_TYPE="Bearer"
```

4) Run the CLI
```bash
python -m robinhood_tracker --help
```

### Commands
- `login`: Authenticate and cache session
- `portfolio`: Display positions, equity, and cash
- `buy --symbol AAPL --quantity 1`: Market buy
- `sell --symbol AAPL --quantity 1`: Market sell
- `rebalance --symbols AAPL,MSFT,GOOGL --allocations 40,30,30`: Example strategy

### Trading Bot Commands
- `bot add --symbol AAPL --quantity 10 --stop-loss -5.0 --take-profit 10.0`: Add position to monitor
- `bot remove --symbol AAPL`: Remove position from monitoring
- `bot start --interval 5`: Start bot (checks every 5 minutes)
- `bot stop`: Stop the bot
- `bot status`: Show monitored positions and current P&L
- `bot check`: Manually check all positions once

## MCP (Model Context Protocol) Integration

The project includes a comprehensive MCP adapter for AI model integration.

### Available Tools

The MCP adapter provides 15 trading and portfolio management tools:

#### Portfolio Management
- `get_portfolio` - Get portfolio summary and positions
- `get_health` - Check API server status
- `login` - Authenticate with Robinhood

#### Trading Operations
- `buy_stock` - Buy shares with symbol and quantity
- `sell_stock` - Sell shares with symbol and quantity
- `rebalance_portfolio` - Auto-rebalance to target allocations

#### Trading Bot Management
- `get_bot_status` - Get bot status and monitored positions
- `add_bot_position` - Add position with stop-loss/take-profit
- `remove_bot_position` - Remove position from monitoring
- `start_bot` - Start automated trading bot
- `stop_bot` - Stop automated trading bot
- `check_bot_positions` - Manually check all positions

#### Options Trading
- `get_options_positions` - Get current options holdings
- `get_options_orders` - Get recent options orders
- `get_options_instruments` - Get available options for symbol

### Usage Examples

```bash
# List all available tools
python3 mcp_robinhood_adapter.py --list-tools

# Get portfolio
python3 mcp_robinhood_adapter.py --tool get_portfolio

# Buy stock
python3 mcp_robinhood_adapter.py --tool buy_stock --params '{"symbol": "AAPL", "quantity": 1}'

# Add position to bot
python3 mcp_robinhood_adapter.py --tool add_bot_position --params '{"symbol": "AAPL", "quantity": 1, "stop_loss": 5, "take_profit": 10}'
```

### AI Model Integration

Configure your AI model to use the MCP server:

```json
{
  "mcpServers": {
    "robinhood": {
      "command": "python3",
      "args": ["/path/to/robinhood_tracker/mcp_robinhood_adapter.py"]
    }
  }
}
```

### Security Notes
- Never commit credentials. Use environment variables or a `.env` file not tracked by git.
- Paper mode writes local state to `.paper_state.json`.
- MCP server communicates with Python backend via local HTTP API (127.0.0.1:5000).

### Disclaimer
This is not financial advice. Use at your own risk.


