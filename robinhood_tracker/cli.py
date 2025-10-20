import os
import json
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .client import RobinhoodClient
from .paper import PaperBroker
from .portfolio import PortfolioService
from .strategy import MomentumStrategy
from .bot import TradingBot


console = Console()


def get_broker() -> RobinhoodClient | PaperBroker:
    load_dotenv()
    paper = os.getenv("RH_PAPER", "true").lower() == "true"
    if paper:
        return PaperBroker(state_path=os.path.join(os.getcwd(), ".paper_state.json"))
    return RobinhoodClient(
        username=os.getenv("RH_USERNAME"),
        password=os.getenv("RH_PASSWORD"),
        device_token=os.getenv("RH_DEVICE_TOKEN"),
        session_path=os.path.join(os.getcwd(), ".rh_session.json"),
    )


@click.group()
def main():
    """Robinhood Portfolio Tracker CLI"""


@main.command()
def login():
    broker = get_broker()
    if isinstance(broker, PaperBroker):
        console.print("[green]Paper mode enabled; no login required[/green]")
    else:
        broker.login()
        console.print("[green]Logged in and session cached[/green]")

    # Show portfolio summary after login
    svc = PortfolioService(broker)
    snapshot = svc.get_portfolio_snapshot()

    table = Table(title="Holdings")
    table.add_column("Symbol")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Value", justify="right")

    for pos in snapshot["positions"]:
        table.add_row(
            pos["symbol"],
            f"{pos['quantity']:.4f}",
            f"{pos['average_price']:.2f}",
            f"{pos['market_price']:.2f}",
            f"{pos['market_value']:.2f}",
        )

    console.print(table)
    console.print(
        f"Total Value: ${snapshot['equity']:.2f} (Cash: ${snapshot['cash']:.2f})"
    )


@main.command()
def portfolio():
    broker = get_broker()
    svc = PortfolioService(broker)
    snapshot = svc.get_portfolio_snapshot()

    table = Table(title="Portfolio")
    table.add_column("Symbol")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Value", justify="right")

    for pos in snapshot["positions"]:
        table.add_row(
            pos["symbol"],
            f"{pos['quantity']:.4f}",
            f"{pos['average_price']:.2f}",
            f"{pos['market_price']:.2f}",
            f"{pos['market_value']:.2f}",
        )

    console.print(table)
    console.print(
        f"Cash: ${snapshot['cash']:.2f} | Equity: ${snapshot['equity']:.2f} | Pct Invested: {snapshot['percent_invested']:.1f}%"
    )


@main.command()
@click.option("--symbol", required=True)
@click.option("--quantity", type=float, required=True)
def buy(symbol: str, quantity: float):
    broker = get_broker()
    order = broker.market_buy(symbol, quantity)
    console.print(json.dumps(order, indent=2))


@main.command()
@click.option("--symbol", required=True)
@click.option("--quantity", type=float, required=True)
def sell(symbol: str, quantity: float):
    broker = get_broker()
    order = broker.market_sell(symbol, quantity)
    console.print(json.dumps(order, indent=2))


@main.command()
@click.option("--symbols", required=True, help="Comma-separated list, e.g., AAPL,MSFT")
@click.option("--allocations", required=True, help="Comma weights in %, e.g., 40,30,30")
@click.option("--cash-buffer", type=float, default=2.0, help="% cash to retain")
def rebalance(symbols: str, allocations: str, cash_buffer: float):
    broker = get_broker()
    svc = PortfolioService(broker)
    strat = MomentumStrategy()
    symbols_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    weights = [float(x) / 100.0 for x in allocations.split(",")]

    if len(symbols_list) != len(weights):
        raise click.ClickException("symbols and allocations length mismatch")

    plan = strat.generate_rebalance_plan(
        svc.get_portfolio_snapshot(), symbols_list, weights, cash_buffer
    )
    if not plan:
        console.print("[yellow]No trades required[/yellow]")
        return

    # Execute
    for leg in plan:
        side = leg["side"]
        if side == "buy":
            broker.market_buy(leg["symbol"], leg["quantity"])
        else:
            broker.market_sell(leg["symbol"], leg["quantity"])
    console.print("[green]Rebalance orders submitted[/green]")


@main.group()
def bot():
    """Trading bot commands"""


@bot.command()
@click.option("--symbol", required=True)
@click.option("--quantity", type=float, required=True)
@click.option("--stop-loss", type=float, required=True, help="Stop loss percentage (e.g., -5.0 for 5% loss)")
@click.option("--take-profit", type=float, required=True, help="Take profit percentage (e.g., 10.0 for 10% gain)")
def add(symbol: str, quantity: float, stop_loss: float, take_profit: float):
    """Add a position to the trading bot"""
    broker = get_broker()
    bot = TradingBot(broker)
    
    if bot.add_position(symbol, quantity, stop_loss, take_profit):
        console.print(f"[green]Added {symbol} to bot monitoring[/green]")
        console.print(f"   Quantity: {quantity}")
        console.print(f"   Stop Loss: {stop_loss}%")
        console.print(f"   Take Profit: {take_profit}%")
    else:
        console.print(f"[red]Failed to add {symbol} to bot[/red]")


@bot.command()
@click.option("--symbol", required=True)
def remove(symbol: str):
    """Remove a position from bot monitoring"""
    broker = get_broker()
    bot = TradingBot(broker)
    
    if bot.remove_position(symbol):
        console.print(f"[green]Removed {symbol} from bot monitoring[/green]")
    else:
        console.print(f"[red]Position {symbol} not found[/red]")


@bot.command()
@click.option("--interval", type=int, default=5, help="Check interval in minutes")
def start(interval: int):
    """Start the trading bot"""
    broker = get_broker()
    bot = TradingBot(broker)
    bot.start_monitoring(interval)


@bot.command()
def stop():
    """Stop the trading bot"""
    broker = get_broker()
    bot = TradingBot(broker)
    bot.stop_monitoring()


@bot.command()
def status():
    """Show bot status and monitored positions"""
    broker = get_broker()
    bot = TradingBot(broker)
    status = bot.get_status()
    
    console.print(f"🤖 Bot Status: {'Running' if status['running'] else 'Stopped'}")
    console.print(f"   Positions: {status['active_positions']}/{status['total_positions']}")
    
    if status["positions"]:
        table = Table(title="Monitored Positions")
        table.add_column("Symbol")
        table.add_column("Qty", justify="right")
        table.add_column("Entry Price", justify="right")
        table.add_column("Current Price", justify="right")
        table.add_column("Change %", justify="right")
        table.add_column("Stop Loss", justify="right")
        table.add_column("Take Profit", justify="right")
        
        for pos in status["positions"]:
            if "error" in pos:
                table.add_row(pos["symbol"], "ERROR", "", "", "", "", pos["error"])
            else:
                change_color = "green" if pos["pct_change"] > 0 else "red"
                table.add_row(
                    pos["symbol"],
                    f"{pos['quantity']:.4f}",
                    f"${pos['entry_price']:.2f}",
                    f"${pos['current_price']:.2f}",
                    f"[{change_color}]{pos['pct_change']:+.2f}%[/{change_color}]",
                    f"{pos['stop_loss']:.1f}%",
                    f"{pos['take_profit']:.1f}%"
                )
        
        console.print(table)


@bot.command()
def check():
    """Manually check all positions once"""
    broker = get_broker()
    bot = TradingBot(broker)
    bot.check_all_positions()


