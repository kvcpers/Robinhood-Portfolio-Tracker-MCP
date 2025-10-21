import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from .client import RobinhoodClient
from .paper import PaperBroker
from .portfolio import PortfolioService
from .strategy import MomentumStrategy
from .bot import TradingBot

app = Flask(__name__)
CORS(app)

# Global broker instance
broker = None
portfolio_service = None
trading_bot = None

def get_broker():
    global broker
    if broker is None:
        load_dotenv()
        paper = os.getenv("RH_PAPER", "true").lower() == "true"
        if paper:
            broker = PaperBroker(state_path=os.path.join(os.getcwd(), ".paper_state.json"))
        else:
            broker = RobinhoodClient(
                username=os.getenv("RH_USERNAME"),
                password=os.getenv("RH_PASSWORD"),
                device_token=os.getenv("RH_DEVICE_TOKEN"),
                session_path=os.path.join(os.getcwd(), ".rh_session.json"),
            )
    return broker

def get_portfolio_service():
    global portfolio_service
    if portfolio_service is None:
        portfolio_service = PortfolioService(get_broker())
    return portfolio_service

def get_trading_bot():
    global trading_bot
    if trading_bot is None:
        trading_bot = TradingBot(get_broker())
    return trading_bot

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Robinhood Tracker API is running"})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        broker = get_broker()
        if isinstance(broker, PaperBroker):
            return jsonify({"success": True, "message": "Paper mode enabled; no login required"})
        
        broker.login()
        return jsonify({"success": True, "message": "Logged in and session cached"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    try:
        svc = get_portfolio_service()
        snapshot = svc.get_portfolio_snapshot()
        return jsonify({"success": True, "data": snapshot})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/buy', methods=['POST'])
def buy_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        
        print(f"Buy request: symbol={symbol}, quantity={quantity}")
        
        if not symbol or not quantity:
            return jsonify({"success": False, "error": "Symbol and quantity required"}), 400
        
        broker = get_broker()
        result = broker.market_buy(symbol, quantity)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"Buy error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/sell', methods=['POST'])
def sell_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        
        print(f"Sell request: symbol={symbol}, quantity={quantity}")
        
        if not symbol or not quantity:
            return jsonify({"success": False, "error": "Symbol and quantity required"}), 400
        
        broker = get_broker()
        result = broker.market_sell(symbol, quantity)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"Sell error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/rebalance', methods=['POST'])
def rebalance():
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        allocations = data.get('allocations', [])
        cash_buffer = data.get('cash_buffer', 2.0)
        
        if len(symbols) != len(allocations):
            return jsonify({"success": False, "error": "Symbols and allocations length mismatch"}), 400
        
        broker = get_broker()
        svc = get_portfolio_service()
        strat = MomentumStrategy()
        
        snapshot = svc.get_portfolio_snapshot()
        weights = [w / 100.0 for w in allocations]
        
        plan = strat.generate_rebalance_plan(snapshot, symbols, weights, cash_buffer)
        
        if not plan:
            return jsonify({"success": True, "message": "No trades required", "trades": []})
        
        trades = []
        for leg in plan:
            side = leg["side"]
            if side == "buy":
                result = broker.market_buy(leg["symbol"], leg["quantity"])
            else:
                result = broker.market_sell(leg["symbol"], leg["quantity"])
            trades.append({
                "symbol": leg["symbol"],
                "side": side,
                "quantity": leg["quantity"],
                "result": result
            })
        
        return jsonify({"success": True, "message": "Rebalance orders submitted", "trades": trades})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# Options endpoints
@app.route('/api/options/positions', methods=['GET'])
def get_options_positions():
    try:
        broker = get_broker()
        positions = broker.get_options_positions()
        return jsonify({"success": True, "data": positions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/options/orders', methods=['GET'])
def get_options_orders():
    try:
        broker = get_broker()
        orders = broker.get_options_orders()
        return jsonify({"success": True, "data": orders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/options/instruments/<symbol>', methods=['GET'])
def get_options_instruments(symbol):
    try:
        broker = get_broker()
        instruments = broker.get_options_instruments(symbol)
        return jsonify({"success": True, "data": instruments})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# Bot endpoints
@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    try:
        bot = get_trading_bot()
        status = bot.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bot/add', methods=['POST'])
def bot_add():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        stop_loss = data.get('stop_loss')
        take_profit = data.get('take_profit')
        
        if not all([symbol, quantity, stop_loss, take_profit]):
            return jsonify({"success": False, "error": "All fields required"}), 400
        
        bot = get_trading_bot()
        success = bot.add_position(symbol, quantity, stop_loss, take_profit)
        
        if success:
            return jsonify({"success": True, "message": f"Added {symbol} to bot monitoring"})
        else:
            return jsonify({"success": False, "error": f"Failed to add {symbol} to bot"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bot/remove', methods=['POST'])
def bot_remove():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({"success": False, "error": "Symbol required"}), 400
        
        bot = get_trading_bot()
        success = bot.remove_position(symbol)
        
        if success:
            return jsonify({"success": True, "message": f"Removed {symbol} from bot monitoring"})
        else:
            return jsonify({"success": False, "error": f"Position {symbol} not found"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bot/start', methods=['POST'])
def bot_start():
    try:
        data = request.get_json()
        interval = data.get('interval', 5)
        
        bot = get_trading_bot()
        bot.start_monitoring(interval)
        
        return jsonify({"success": True, "message": f"Bot started with {interval} minute intervals"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bot/stop', methods=['POST'])
def bot_stop():
    try:
        bot = get_trading_bot()
        bot.stop_monitoring()
        
        return jsonify({"success": True, "message": "Bot stopped"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bot/check', methods=['POST'])
def bot_check():
    try:
        bot = get_trading_bot()
        bot.check_all_positions()
        
        return jsonify({"success": True, "message": "Manual check completed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
