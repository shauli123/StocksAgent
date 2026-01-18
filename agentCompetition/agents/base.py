from abc import ABC, abstractmethod
import pandas as pd

class BaseAgent(ABC):
    def __init__(self, name, config):
        self.name = name
        self.cash = config.get('cash', 10000)
        self.portfolio_value = config.get('portfolio_value', 10000)
        self.holdings = config.get('holdings', {}) # {symbol: shares}
        self.color = config.get('color', '#000000')
        self.description = config.get('description', '')
        self.trades = []

    def update_portfolio_value(self, current_prices):
        """
        Updates portfolio value based on current market prices.
        current_prices: dict {symbol: price}
        """
        holdings_value = 0
        for symbol, shares in self.holdings.items():
            if symbol in current_prices:
                holdings_value += shares * current_prices[symbol]
        
        self.portfolio_value = self.cash + holdings_value
        return self.portfolio_value

    def execute_trade(self, symbol, action, price, shares, date):
        """
        Records a trade and updates cash/holdings.
        action: 'BUY' or 'SELL'
        """
        cost = price * shares
        
        if action == 'BUY':
            if self.cash >= cost:
                self.cash -= cost
                self.holdings[symbol] = self.holdings.get(symbol, 0) + shares
                self.trades.append({
                    'date': date, 'symbol': symbol, 'action': 'BUY', 
                    'price': price, 'shares': shares, 'agent': self.name
                })
                return True
        elif action == 'SELL':
            if self.holdings.get(symbol, 0) >= shares:
                self.cash += cost
                self.holdings[symbol] -= shares
                if self.holdings[symbol] == 0:
                    del self.holdings[symbol]
                self.trades.append({
                    'date': date, 'symbol': symbol, 'action': 'SELL', 
                    'price': price, 'shares': shares, 'agent': self.name
                })
                return True
        return False

    @abstractmethod
    def decide(self, market_data):
        """
        Decides on trades based on market data.
        market_data: dict {symbol: dataframe}
        Returns: list of orders [{'symbol': 'AAPL', 'action': 'BUY', 'shares': 10}, ...]
        """
        pass
