from typing import Dict, Any, List, Protocol


class BrokerLike(Protocol):
    def get_positions(self) -> Dict[str, Any]: ...
    def get_quote(self, symbol: str) -> float: ...


class PortfolioService:
    def __init__(self, broker: BrokerLike) -> None:
        self.broker = broker

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        data = self.broker.get_positions()
        positions_raw = data.get("results", [])
        positions: List[Dict[str, Any]] = []
        equity = 0.0
        for row in positions_raw:
            symbol = row.get("symbol") or row.get("instrument", "").split("/")[-2]
            quantity = float(row.get("quantity") or row.get("quantity_available") or 0.0)
            avg_price = float(row.get("average_buy_price") or 0.0)
            try:
                price = self.broker.get_quote(symbol)
                value = price * quantity
                equity += value
                positions.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "average_price": avg_price,
                    "market_price": price,
                    "market_value": value,
                })
            except Exception as e:
                # Skip positions with invalid symbols or quote errors
                print(f"Warning: Could not get quote for {symbol}: {e}")
                continue
        # Cash only known in paper mode; for live we'd fetch accounts and portfolio endpoints
        cash = getattr(self.broker, "state", {}).get("cash", 0.0)
        invested_pct = (equity / (equity + cash) * 100.0) if (equity + cash) > 0 else 0.0
        return {
            "positions": positions,
            "cash": cash,
            "equity": equity + cash,
            "percent_invested": invested_pct,
        }


