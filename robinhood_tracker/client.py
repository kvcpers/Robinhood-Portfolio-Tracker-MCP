import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

import requests
from tenacity import retry, wait_exponential, stop_after_attempt


ROBINHOOD_API = "https://api.robinhood.com"


class AuthError(Exception):
    pass


@dataclass
class RobinhoodClient:
    username: Optional[str]
    password: Optional[str]
    device_token: Optional[str]
    session_path: str

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.token_type: str = ""
        # Load token from environment first, then session file
        self.load_env_token()
        self.load_session()

    def load_session(self) -> None:
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, "r") as f:
                    data = json.load(f)
                self.access_token = data.get("access_token")
                self.token_type = data.get("token_type", "")
                if self.access_token:
                    self.session.headers.update(
                        {"Authorization": f"{self.token_type} {self.access_token}"}
                    )
            except Exception:
                pass

    def load_env_token(self) -> None:
        env_token = os.getenv("RH_ACCESS_TOKEN")
        if env_token:
            self.access_token = env_token
            self.token_type = os.getenv("RH_TOKEN_TYPE", "Bearer")
            self.session.headers.update(
                {"Authorization": f"{self.token_type} {self.access_token}"}
            )

    def save_session(self, payload: Dict[str, Any]) -> None:
        with open(self.session_path, "w") as f:
            json.dump({
                "access_token": payload.get("access_token"),
                "token_type": payload.get("token_type", "Bearer"),
                "timestamp": int(time.time()),
            }, f)

    def ensure_auth(self) -> None:
        if not self.access_token:
            self.login()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def login(self) -> None:
        # If an access token is already present (from env or session), skip login
        if self.access_token:
            return
        if not self.username or not self.password:
            raise AuthError("Missing RH_USERNAME/RH_PASSWORD")

        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
            "scope": "internal",
            "client_id": "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
        }
        if self.device_token:
            payload["device_token"] = self.device_token

        resp = self.session.post(f"{ROBINHOOD_API}/oauth2/token/", data=payload, timeout=30)
        if resp.status_code == 403:
            try:
                error_data = resp.json()
                if "verification_workflow" in error_data:
                    workflow_id = error_data["verification_workflow"]["id"]
                    raise AuthError(f"Verification required. Please check your email or complete MFA in the Robinhood app. Workflow ID: {workflow_id}")
            except:
                pass
            raise AuthError(f"Login failed: 403 Forbidden. Check your credentials and complete any required verification.")
        elif resp.status_code >= 400:
            raise AuthError(f"Login failed: {resp.status_code} {resp.text}")
        data = resp.json()
        self.access_token = data["access_token"]
        self.token_type = data.get("token_type", "Bearer")
        self.session.headers.update({"Authorization": f"{self.token_type} {self.access_token}"})
        self.save_session(data)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_auth()
        resp = self.session.get(f"{ROBINHOOD_API}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_auth()
        resp = self.session.post(f"{ROBINHOOD_API}{path}", data=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # Simplified endpoints
    def get_accounts(self) -> Dict[str, Any]:
        return self._get("/accounts/")

    def get_positions(self) -> Dict[str, Any]:
        return self._get("/positions/")

    def get_portfolio(self) -> Dict[str, Any]:
        return self._get("/portfolios/")

    def get_instrument_by_symbol(self, symbol: str) -> Optional[str]:
        data = self._get("/instruments/", params={"symbol": symbol})
        results = data.get("results", [])
        if not results:
            return None
        return results[0]["url"]

    def get_quote(self, symbol: str) -> float:
        data = self._get("/marketdata/quotes/", params={"symbols": symbol})
        results = data.get("results", [])
        if not results:
            raise ValueError(f"No quote for {symbol}")
        return float(results[0]["last_trade_price"])  # market proxy

    def place_order(self, symbol: str, quantity: float, side: str) -> Dict[str, Any]:
        instrument_url = self.get_instrument_by_symbol(symbol)
        if not instrument_url:
            raise ValueError(f"Unknown symbol {symbol}")
        payload = {
            "account": self.get_accounts()["results"][0]["url"],
            "instrument": instrument_url,
            "symbol": symbol,
            "type": "market",
            "time_in_force": "gfd",
            "trigger": "immediate",
            "quantity": str(quantity),
            "side": side,
        }
        return self._post("/orders/", payload)

    # Friendly wrappers
    def market_buy(self, symbol: str, quantity: float) -> Dict[str, Any]:
        return self.place_order(symbol, quantity, side="buy")

    def market_sell(self, symbol: str, quantity: float) -> Dict[str, Any]:
        return self.place_order(symbol, quantity, side="sell")

    def get_options_positions(self) -> Dict[str, Any]:
        """Get options positions from Robinhood"""
        return self._get("/options/positions/")

    def get_options_orders(self) -> Dict[str, Any]:
        """Get options orders from Robinhood"""
        return self._get("/options/orders/")

    def get_options_instruments(self, symbol: str) -> Dict[str, Any]:
        """Get options instruments for a symbol"""
        return self._get("/options/instruments/", params={"equity_instrument": self.get_instrument_by_symbol(symbol)})


