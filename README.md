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

### Security Notes
- Never commit credentials. Use environment variables or a `.env` file not tracked by git.
- Paper mode writes local state to `.paper_state.json`.

### Disclaimer
This is not financial advice. Use at your own risk.


