import json
import os
from typing import Dict, Any


class PaperBroker:
    def __init__(self, state_path: str) -> None:
        self.state_path = state_path
        self.state = {"cash": 100000.0, "positions": {}}  # symbol -> {qty, avg_price}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    self.state = json.load(f)
            except Exception:
                pass

    def _save(self) -> None:
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2)

    def login(self) -> None:
        return

    def get_quote(self, symbol: str) -> float:
        # Very naive mock price using hash for determinism
        base = 100 + (abs(hash(symbol)) % 500) / 10.0
        return round(base, 2)

    def get_positions(self) -> Dict[str, Any]:
        return {"results": [
            {
                "symbol": s,
                "quantity": str(p["qty"]),
                "average_buy_price": str(p["avg_price"]),
            }
            for s, p in self.state["positions"].items()
        ]}

    def get_accounts(self) -> Dict[str, Any]:
        # minimal stub
        return {"results": [{"url": "paper://account/1"}]}

    def market_buy(self, symbol: str, quantity: float) -> Dict[str, Any]:
        price = self.get_quote(symbol)
        cost = price * quantity
        if cost > self.state["cash"]:
            raise ValueError("Insufficient cash in paper account")
        pos = self.state["positions"].get(symbol, {"qty": 0.0, "avg_price": 0.0})
        new_qty = pos["qty"] + quantity
        new_avg = (
            (pos["qty"] * pos["avg_price"] + cost) / new_qty if new_qty > 0 else 0.0
        )
        self.state["positions"][symbol] = {"qty": new_qty, "avg_price": new_avg}
        self.state["cash"] -= cost
        self._save()
        return {"symbol": symbol, "quantity": quantity, "side": "buy", "price": price}

    def market_sell(self, symbol: str, quantity: float) -> Dict[str, Any]:
        price = self.get_quote(symbol)
        pos = self.state["positions"].get(symbol)
        if not pos or pos["qty"] < quantity:
            raise ValueError("Insufficient shares in paper account")
        pos["qty"] -= quantity
        if pos["qty"] <= 0:
            del self.state["positions"][symbol]
        else:
            self.state["positions"][symbol] = pos
        proceeds = price * quantity
        self.state["cash"] += proceeds
        self._save()
        return {"symbol": symbol, "quantity": quantity, "side": "sell", "price": price}


