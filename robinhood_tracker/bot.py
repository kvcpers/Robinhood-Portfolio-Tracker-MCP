import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import schedule

from .client import RobinhoodClient
from .paper import PaperBroker


@dataclass
class BotConfig:
    symbol: str
    quantity: float
    stop_loss_pct: float  # e.g., -5.0 for 5% stop loss
    take_profit_pct: float  # e.g., 10.0 for 10% profit target
    entry_price: float
    is_active: bool = True
    created_at: str = ""
    last_check: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_check:
            self.last_check = datetime.now().isoformat()


class TradingBot:
    def __init__(self, broker: RobinhoodClient | PaperBroker, config_path: str = ".bot_config.json"):
        self.broker = broker
        self.config_path = config_path
        self.configs: Dict[str, BotConfig] = {}
        self.running = False
        self.thread = None
        self.load_configs()

    def load_configs(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    for symbol, config_data in data.items():
                        self.configs[symbol] = BotConfig(**config_data)
            except Exception as e:
                print(f"Error loading bot configs: {e}")

    def save_configs(self) -> None:
        data = {symbol: asdict(config) for symbol, config in self.configs.items()}
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_position(self, symbol: str, quantity: float, stop_loss_pct: float, take_profit_pct: float) -> bool:
        """Add a new position to monitor"""
        try:
            # Get current price
            current_price = self.broker.get_quote(symbol)
            
            config = BotConfig(
                symbol=symbol.upper(),
                quantity=quantity,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                entry_price=current_price
            )
            
            self.configs[symbol.upper()] = config
            self.save_configs()
            return True
        except Exception as e:
            print(f"Error adding position {symbol}: {e}")
            return False

    def remove_position(self, symbol: str) -> bool:
        """Remove a position from monitoring"""
        symbol = symbol.upper()
        if symbol in self.configs:
            del self.configs[symbol]
            self.save_configs()
            return True
        return False

    def check_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Check a single position for stop-loss or take-profit triggers"""
        config = self.configs.get(symbol.upper())
        if not config or not config.is_active:
            return None

        try:
            current_price = self.broker.get_quote(symbol)
            config.last_check = datetime.now().isoformat()
            
            # Calculate percentage change
            pct_change = ((current_price - config.entry_price) / config.entry_price) * 100
            
            action = None
            reason = ""
            
            # Check stop loss
            if pct_change <= config.stop_loss_pct:
                action = "sell"
                reason = f"Stop loss triggered: {pct_change:.2f}% <= {config.stop_loss_pct}%"
            
            # Check take profit
            elif pct_change >= config.take_profit_pct:
                action = "sell"
                reason = f"Take profit triggered: {pct_change:.2f}% >= {config.take_profit_pct}%"
            
            if action:
                return {
                    "symbol": symbol,
                    "action": action,
                    "quantity": config.quantity,
                    "current_price": current_price,
                    "entry_price": config.entry_price,
                    "pct_change": pct_change,
                    "reason": reason
                }
            
            return {
                "symbol": symbol,
                "action": "hold",
                "current_price": current_price,
                "entry_price": config.entry_price,
                "pct_change": pct_change,
                "reason": "No trigger conditions met"
            }
            
        except Exception as e:
            print(f"Error checking position {symbol}: {e}")
            return None

    def execute_trade(self, trade_info: Dict[str, Any]) -> bool:
        """Execute a trade based on bot decision"""
        try:
            symbol = trade_info["symbol"]
            action = trade_info["action"]
            quantity = trade_info["quantity"]
            
            if action == "sell":
                result = self.broker.market_sell(symbol, quantity)
                print(f"🤖 BOT SOLD {quantity} shares of {symbol} at ${trade_info['current_price']:.2f}")
                print(f"   Reason: {trade_info['reason']}")
                print(f"   P&L: {trade_info['pct_change']:.2f}%")
                
                # Remove from monitoring after selling
                self.remove_position(symbol)
                return True
            elif action == "buy":
                result = self.broker.market_buy(symbol, quantity)
                print(f"🤖 BOT BOUGHT {quantity} shares of {symbol} at ${trade_info['current_price']:.2f}")
                return True
                
        except Exception as e:
            print(f"Error executing trade for {trade_info.get('symbol', 'unknown')}: {e}")
            return False
        
        return False

    def check_all_positions(self) -> None:
        """Check all monitored positions"""
        if not self.configs:
            return
            
        print(f"\n🔍 Checking {len(self.configs)} positions at {datetime.now().strftime('%H:%M:%S')}")
        
        for symbol in list(self.configs.keys()):
            result = self.check_position(symbol)
            if result and result["action"] != "hold":
                self.execute_trade(result)
            elif result:
                print(f"   {symbol}: {result['pct_change']:+.2f}% (HOLD)")

    def start_monitoring(self, interval_minutes: int = 5) -> None:
        """Start the monitoring loop"""
        if self.running:
            print("Bot is already running!")
            return
            
        self.running = True
        print(f"🤖 Starting trading bot (checking every {interval_minutes} minutes)")
        print(f"   Monitoring {len(self.configs)} positions")
        
        # Schedule the check
        schedule.every(interval_minutes).minutes.do(self.check_all_positions)
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()

    def stop_monitoring(self) -> None:
        """Stop the monitoring loop"""
        self.running = False
        schedule.clear()
        if self.thread:
            self.thread.join(timeout=1)
        print("🤖 Trading bot stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        active_positions = [config for config in self.configs.values() if config.is_active]
        
        status = {
            "running": self.running,
            "total_positions": len(self.configs),
            "active_positions": len(active_positions),
            "positions": []
        }
        
        for config in active_positions:
            try:
                current_price = self.broker.get_quote(config.symbol)
                pct_change = ((current_price - config.entry_price) / config.entry_price) * 100
                
                status["positions"].append({
                    "symbol": config.symbol,
                    "quantity": config.quantity,
                    "entry_price": config.entry_price,
                    "current_price": current_price,
                    "pct_change": pct_change,
                    "stop_loss": config.stop_loss_pct,
                    "take_profit": config.take_profit_pct,
                    "last_check": config.last_check
                })
            except Exception as e:
                status["positions"].append({
                    "symbol": config.symbol,
                    "error": str(e)
                })
        
        return status
