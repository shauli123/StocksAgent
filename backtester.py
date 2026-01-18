import pandas as pd

class Backtester:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.portfolio_value = initial_capital
        self.cash = initial_capital
        self.position = 0 # Number of shares
        self.trades = []

    def run(self, df):
        """
        Runs the backtest on the dataframe with 'Signal' column.
        """
        df = df.copy()
        df['Portfolio Value'] = self.initial_capital
        
        for index, row in df.iterrows():
            price = row['Close']
            signal = row['Signal']
            
            if signal == 1 and self.cash > price: # Buy
                # Buy as much as possible
                shares_to_buy = self.cash // price
                cost = shares_to_buy * price
                self.cash -= cost
                self.position += shares_to_buy
                self.trades.append({'Date': index, 'Type': 'BUY', 'Price': price, 'Shares': shares_to_buy})
                
            elif signal == -1 and self.position > 0: # Sell
                # Sell all
                revenue = self.position * price
                self.cash += revenue
                self.trades.append({'Date': index, 'Type': 'SELL', 'Price': price, 'Shares': self.position})
                self.position = 0
            
            current_value = self.cash + (self.position * price)
            df.at[index, 'Portfolio Value'] = current_value
            
        self.portfolio_value = df.iloc[-1]['Portfolio Value']
        return df, self.trades

    def get_performance_metrics(self):
        return {
            'Final Portfolio Value': self.portfolio_value,
            'Return (%)': ((self.portfolio_value - self.initial_capital) / self.initial_capital) * 100,
            'Total Trades': len(self.trades)
        }
