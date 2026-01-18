import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {} # {symbol: shares}
        self.trades = []
        self.portfolio_history = []

    def run(self, data_dict):
        """
        Runs the backtest on a dictionary of dataframes {symbol: df}.
        Each df must have a 'Signal' column.
        """
        # 1. Align Dates
        # Get all unique dates from all dataframes
        all_dates = sorted(list(set().union(*[df.index.tolist() for df in data_dict.values()])))
        
        print(f"Backtesting over {len(all_dates)} days...")
        
        for date in all_dates:
            daily_value = self.cash
            
            for symbol, df in data_dict.items():
                if date not in df.index:
                    # Stock might not trade today or data missing
                    if symbol in self.positions:
                         # Use last known price if possible, or just skip valuation update for this stock today?
                         # For simplicity, we skip trading but we need price for valuation.
                         # We'll assume if date is missing, price didn't change (or we can't trade).
                         pass
                    continue
                
                row = df.loc[date]
                price = row['Close']
                signal = row.get('Signal', 0)
                
                # Execute Trades
                if signal == 1: # Buy
                    # Simple money management: Allocate 20% of current cash per trade
                    # Or allocate fixed amount? Let's do 20% of *initial* capital to allow multiple positions
                    allocation = self.initial_capital * 0.2
                    
                    if self.cash >= allocation:
                        shares_to_buy = int(allocation // price)
                        if shares_to_buy > 0:
                            cost = shares_to_buy * price
                            self.cash -= cost
                            self.positions[symbol] = self.positions.get(symbol, 0) + shares_to_buy
                            self.trades.append({
                                'Date': date, 'Symbol': symbol, 'Type': 'BUY', 
                                'Price': price, 'Shares': shares_to_buy
                            })
                            
                elif signal == -1: # Sell
                    current_shares = self.positions.get(symbol, 0)
                    if current_shares > 0:
                        revenue = current_shares * price
                        self.cash += revenue
                        self.positions[symbol] = 0
                        self.trades.append({
                            'Date': date, 'Symbol': symbol, 'Type': 'SELL', 
                            'Price': price, 'Shares': current_shares
                        })
                
                # Update Valuation
                # We add the value of current holdings for this symbol
                daily_value += self.positions.get(symbol, 0) * price
            
            self.portfolio_history.append({'Date': date, 'Portfolio Value': daily_value})
            
        # Create history dataframe
        history_df = pd.DataFrame(self.portfolio_history)
        if not history_df.empty:
            history_df.set_index('Date', inplace=True)
            
        return history_df, self.trades

    def get_performance_metrics(self, history_df):
        if history_df.empty:
            return {}
            
        final_value = history_df.iloc[-1]['Portfolio Value']
        return {
            'Final Portfolio Value': final_value,
            'Return (%)': ((final_value - self.initial_capital) / self.initial_capital) * 100,
            'Total Trades': len(self.trades)
        }
