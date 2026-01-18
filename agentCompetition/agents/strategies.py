from .base import BaseAgent
import pandas as pd

class BasicAgent(BaseAgent):
    """
    Simple SMA Crossover Strategy.
    Buy: SMA_20 > SMA_50
    Sell: SMA_20 < SMA_50
    """
    def decide(self, market_data):
        orders = []
        for symbol, df in market_data.items():
            if df.empty: continue
            row = df.iloc[-1]
            price = row['Close']
            
            # Check if we have enough data for SMAs
            if pd.isna(row.get('SMA_20')) or pd.isna(row.get('SMA_50')):
                continue
                
            # Logic
            if row['SMA_20'] > row['SMA_50']:
                # Buy Signal
                if symbol not in self.holdings and self.cash > price:
                    # Simple allocation: 10% of initial capital (fixed)
                    shares = int(1000 / price) 
                    if shares > 0 and self.cash >= shares * price:
                        orders.append({'symbol': symbol, 'action': 'BUY', 'shares': shares})
            elif row['SMA_20'] < row['SMA_50']:
                # Sell Signal
                if symbol in self.holdings:
                    orders.append({'symbol': symbol, 'action': 'SELL', 'shares': self.holdings[symbol]})
        return orders

class ProAgent(BaseAgent):
    """
    Scored Strategy + ATR Trailing Stop (2.0).
    """
    def __init__(self, name, config):
        super().__init__(name, config)
        self.trailing_stops = {} # {symbol: highest_price}

    def decide(self, market_data):
        orders = []
        for symbol, df in market_data.items():
            if df.empty: continue
            row = df.iloc[-1]
            price = row['Close']
            atr = row.get('ATR', 0)
            score = 0
            
            # Update Trailing Stop
            if symbol in self.holdings:
                if symbol not in self.trailing_stops:
                    self.trailing_stops[symbol] = price
                if price > self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = price
                
                stop_price = self.trailing_stops[symbol] - (atr * 2.0)
                if price < stop_price:
                    orders.append({'symbol': symbol, 'action': 'SELL', 'shares': self.holdings[symbol]})
                    continue

            # Scoring
            if row['SMA_20'] > row['SMA_50']: score += 2
            if row['RSI'] < 30: score += 2
            if row['RSI'] > 70: score -= 2
            
            # Buy
            if score >= 3 and symbol not in self.holdings:
                shares = int(2000 / price) # 20% allocation
                if shares > 0 and self.cash >= shares * price:
                    orders.append({'symbol': symbol, 'action': 'BUY', 'shares': shares})
                    self.trailing_stops[symbol] = price
            
            # Sell (Score based)
            elif score <= 0 and symbol in self.holdings:
                 orders.append({'symbol': symbol, 'action': 'SELL', 'shares': self.holdings[symbol]})
                 
        return orders

class AggressiveAgent(BaseAgent):
    """
    Compounding + ATR 4.0 + Threshold 2.
    """
    def __init__(self, name, config):
        super().__init__(name, config)
        self.trailing_stops = {}

    def decide(self, market_data):
        orders = []
        for symbol, df in market_data.items():
            if df.empty: continue
            row = df.iloc[-1]
            price = row['Close']
            atr = row.get('ATR', 0)
            score = 0
            
            # Trailing Stop (ATR 4.0)
            if symbol in self.holdings:
                if symbol not in self.trailing_stops:
                    self.trailing_stops[symbol] = price
                if price > self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = price
                
                stop_price = self.trailing_stops[symbol] - (atr * 4.0)
                if price < stop_price:
                    orders.append({'symbol': symbol, 'action': 'SELL', 'shares': self.holdings[symbol]})
                    continue

            # Scoring (Aggressive)
            if row['SMA_20'] > row['SMA_50']: score += 2
            if row['SMA_20'] > row['SMA_50'] and price > row['SMA_20']: score += 1 # Strong Trend
            if row['RSI'] > 50 and row['RSI'] < 70: score += 1 # Healthy Momentum
            if row['RSI'] < 30: score += 2
            if row['RSI'] > 70: score -= 2
            
            # Buy (Threshold 2)
            if score >= 2 and symbol not in self.holdings:
                # Compounding: 30% of AVAILABLE CASH
                allocation = self.cash * 0.30
                if allocation > 1000: # Min trade size
                    shares = int(allocation / price)
                    if shares > 0:
                        orders.append({'symbol': symbol, 'action': 'BUY', 'shares': shares})
                        self.trailing_stops[symbol] = price
            
            # Sell
            elif score <= 0 and symbol in self.holdings:
                 orders.append({'symbol': symbol, 'action': 'SELL', 'shares': self.holdings[symbol]})

        return orders

class Mag7Agent(AggressiveAgent):
    """
    Same as Aggressive, but only trades Mag 7 stocks.
    """
    MAG7 = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    
    def decide(self, market_data):
        # Filter market data for Mag 7 only
        filtered_data = {k: v for k, v in market_data.items() if k in self.MAG7}
        return super().decide(filtered_data)
