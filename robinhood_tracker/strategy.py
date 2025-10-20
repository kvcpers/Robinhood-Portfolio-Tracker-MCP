from typing import Dict, Any, List


class MomentumStrategy:
    def generate_rebalance_plan(
        self,
        snapshot: Dict[str, Any],
        symbols: List[str],
        target_weights: List[float],
        cash_buffer_pct: float = 2.0,
    ) -> List[Dict[str, Any]]:
        positions = {p["symbol"]: p for p in snapshot["positions"]}
        cash = snapshot["cash"]
        equity = snapshot["equity"]
        investable = equity * (1 - cash_buffer_pct / 100.0)

        desired_values = {s: w * investable for s, w in zip(symbols, target_weights)}

        plan: List[Dict[str, Any]] = []
        for symbol in symbols:
            target_value = desired_values.get(symbol, 0.0)
            price = positions.get(symbol, {"market_price": 0.0}).get("market_price", 0.0)
            if price <= 0:
                # skip symbols we don't have a price for
                continue
            target_qty = target_value / price
            current_qty = positions.get(symbol, {"quantity": 0.0}).get("quantity", 0.0)
            delta = target_qty - current_qty
            if abs(delta) * price < 10:  # skip tiny trades under $10 notionals
                continue
            side = "buy" if delta > 0 else "sell"
            plan.append({"symbol": symbol, "side": side, "quantity": abs(delta)})

        return plan


