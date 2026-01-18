import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=10000, trailing_stop_atr_multiplier=4.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {} # {symbol: shares}
        self.position_metadata = {} # {symbol: {'highest_price': float, 'entry_price': float}}
        self.trades = []
        self.portfolio_history = []
        self.trailing_stop_atr_multiplier = trailing_stop_atr_multiplier

    def run(self, data_dict):
        """
        Runs the backtest on a dictionary of dataframes {symbol: df}.
        """
        # 1. Align Dates
        all_dates = sorted(list(set().union(*[df.index.tolist() for df in data_dict.values()])))
        
        print(f"Backtesting over {len(all_dates)} days...")
        
        for date in all_dates:
            daily_value = self.cash
            
            for symbol, df in data_dict.items():
                if date not in df.index:
                    if symbol in self.positions:
                         # Use last known price for valuation if possible
                         pass
                    continue
                
                row = df.loc[date]
                price = row['Close']
                signal = row.get('Signal', 0)
                atr = row.get('ATR', 0)
                
                # Check Trailing Stop
                if symbol in self.positions:
                    # Update highest price since entry
                    if price > self.position_metadata[symbol]['highest_price']:
                        self.position_metadata[symbol]['highest_price'] = price
                    
                    # Check if stop hit
                    stop_price = self.position_metadata[symbol]['highest_price'] - (atr * self.trailing_stop_atr_multiplier)
                    
                    if price < stop_price:
                        # Trigger Sell (Stop Loss)
                        # print(f"Trailing Stop Hit for {symbol} at {price:.2f} (Stop: {stop_price:.2f})")
                        signal = -1 # Override signal
                
                # Execute Trades
                if signal == 1: # Buy
                    # Aggressive Compounding: Invest 30% of AVAILABLE CASH per trade
                    allocation = self.cash * 0.3
                    
                    # Ensure minimum trade size to avoid tiny trades
                    if allocation > 1000 and symbol not in self.positions:
                        shares_to_buy = int(allocation // price)
                        if shares_to_buy > 0:
                            cost = shares_to_buy * price
                            self.cash -= cost
                            self.positions[symbol] = shares_to_buy
                            self.position_metadata[symbol] = {'highest_price': price, 'entry_price': price}
                            self.trades.append({
                                'Date': date, 'Symbol': symbol, 'Type': 'BUY', 
                                'Price': price, 'Shares': shares_to_buy
                            })
                            
                elif signal == -1: # Sell
                    current_shares = self.positions.get(symbol, 0)
                    if current_shares > 0:
                        revenue = current_shares * price
                        self.cash += revenue
                        del self.positions[symbol]
                        del self.position_metadata[symbol]
                        self.trades.append({
                            'Date': date, 'Symbol': symbol, 'Type': 'SELL', 
                            'Price': price, 'Shares': current_shares
                        })
                
                # Update Valuation
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
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        days = len(history_df)
        
        # Gain Per Day ($)
        gain_per_day = (final_value - self.initial_capital) / days if days > 0 else 0
        
        # Max Drawdown
        rolling_max = history_df['Portfolio Value'].cummax()
        drawdown = (history_df['Portfolio Value'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'Final Portfolio Value': final_value,
            'Return (%)': total_return,
            'Gain Per Day ($)': gain_per_day,
            'Max Drawdown (%)': max_drawdown,
            'Total Trades': len(self.trades)
        }
