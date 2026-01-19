from flask import Flask, jsonify, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

# Data Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
AGENTS_FILE = os.path.join(DATA_DIR, 'agents.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
TRADES_FILE = os.path.join(DATA_DIR, 'trades.json')

def load_json(filepath, default=None):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    agents = load_json(AGENTS_FILE, {})
    history = load_json(HISTORY_FILE, {})
    trades = load_json(TRADES_FILE, [])
    return jsonify({'agents': agents, 'history': history, 'trades': trades})

from agents import BasicAgent, ProAgent, AggressiveAgent, Mag7Agent
from agents.data_loader import fetch_stock_data, get_sp500_tickers
from agents.technical_analysis import add_technical_indicators
import pandas as pd
from datetime import datetime, timedelta
import random

# Fetch S&P 500 once on startup
try:
    SP500_TICKERS = get_sp500_tickers()
    if not SP500_TICKERS:
        raise Exception("Failed to fetch S&P 500")
    print(f"Loaded {len(SP500_TICKERS)} S&P 500 stocks.")
except:
    print("Fallback to Tech Universe")
    SP500_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC', 
                     'IBM', 'ORCL', 'CSCO', 'ADBE', 'CRM', 'QCOM', 'TXN', 'AVGO', 'PYPL', 'SBUX']

import threading
import time

def run_trade_cycle():
    """
    Core trading logic, decoupled from Flask request context.
    """
    try:
        # 1. Load State
        agents_data = load_json(AGENTS_FILE, {})
        history = load_json(HISTORY_FILE, {})
        trades_log = load_json(TRADES_FILE, [])
        
        # Initialize Agents
        agents = {
            "BasicAgent": BasicAgent("BasicAgent", agents_data.get("BasicAgent", {})),
            "ProAgent": ProAgent("ProAgent", agents_data.get("ProAgent", {})),
            "AggressiveAgent": AggressiveAgent("AggressiveAgent", agents_data.get("AggressiveAgent", {})),
            "Mag7Agent": Mag7Agent("Mag7Agent", agents_data.get("Mag7Agent", {}))
        }
        
        # 2. Fetch Market Data (Batch of 50)
        batch_size = 50
        universe_batch = random.sample(SP500_TICKERS, min(len(SP500_TICKERS), batch_size))
        mag7 = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META']
        universe_batch = list(set(universe_batch + mag7))
        
        print(f"Scanning batch of {len(universe_batch)} stocks...")
        
        market_data = {}
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d') 
        
        current_prices = {}
        
        errors = []
        for symbol in universe_batch:
            try:
                df = fetch_stock_data(symbol, start_date, end_date)
                if not df.empty:
                    df = add_technical_indicators(df)
                    market_data[symbol] = df
                    current_prices[symbol] = df.iloc[-1]['Close']
                else:
                    errors.append(f"{symbol}: Empty DF")
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")

        if not market_data:
            return {'status': 'Error', 'message': 'No market data fetched', 'details': errors[:5]}

        # 3. Run Agents
        timestamp = datetime.now().isoformat()
        new_trades = []
        
        for name, agent in agents.items():
            # Decide
            orders = agent.decide(market_data)
            
            # Execute
            for order in orders:
                symbol = order['symbol']
                action = order['action']
                shares = order['shares']
                price = current_prices.get(symbol)
                
                if price:
                    if agent.execute_trade(symbol, action, price, shares, timestamp):
                        trade_record = {
                            'date': timestamp,
                            'agent': name,
                            'symbol': symbol,
                            'action': action,
                            'shares': shares,
                            'price': price,
                            'total': shares * price
                        }
                        new_trades.append(trade_record)
                        trades_log.append(trade_record)

            # Update Portfolio Value
            agent.update_portfolio_value(current_prices)
            
            # Calculate Revenue Per Day
            start_value = agents_data.get(name, {}).get('start_value', 10000)
            revenue = agent.portfolio_value - start_value
            
            # Update State Dict
            agents_data[name] = {
                "cash": agent.cash,
                "portfolio_value": agent.portfolio_value,
                "holdings": agent.holdings,
                "color": agent.color,
                "description": agent.description,
                "start_value": start_value,
                "revenue": revenue
            }
            
            # Update History
            if name not in history: history[name] = []
            history[name].append({'date': timestamp, 'value': agent.portfolio_value})

        # 4. Save State
        save_json(AGENTS_FILE, agents_data)
        save_json(HISTORY_FILE, history)
        save_json(TRADES_FILE, trades_log)
        
        return {
            'status': 'Success', 
            'timestamp': timestamp, 
            'trades_executed': len(new_trades),
            'new_trades': new_trades
        }
        
    except Exception as e:
        print(f"Trade Cycle Error: {e}")
        return {'status': 'Error', 'message': str(e)}

@app.route('/api/trade')
def trigger_trade():
    """
    Manual trigger endpoint.
    """
    result = run_trade_cycle()
    return jsonify(result)

def background_trader():
    """
    Runs the trading cycle every 10 seconds in the background.
    """
    print("Starting Background Auto-Trader...")
    while True:
        run_trade_cycle()
        time.sleep(10)

if __name__ == '__main__':
    # Start background thread
    t = threading.Thread(target=background_trader, daemon=True)
    t.start()
    
    app.run(debug=True, use_reloader=False) # use_reloader=False prevents double execution
