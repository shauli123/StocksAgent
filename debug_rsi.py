from data_loader import fetch_stock_data
from technical_analysis import add_technical_indicators
import pandas as pd

# Fetch data
df = fetch_stock_data("AAPL", "2023-01-01", "2023-06-01")
print(f"Rows fetched: {len(df)}")

if not df.empty:
    # Add indicators
    df = add_technical_indicators(df)
    
    # Check RSI stats
    print(f"RSI Min: {df['RSI'].min()}")
    print(f"RSI Max: {df['RSI'].max()}")
    print(f"RSI Mean: {df['RSI'].mean()}")
    
    # Check if any hit the default thresholds (30/70)
    buys = df[df['RSI'] < 30]
    sells = df[df['RSI'] > 70]
    
    print(f"Potential Buys (<30): {len(buys)}")
    print(f"Potential Sells (>70): {len(sells)}")
    
    if len(buys) > 0:
        print("Buy Dates:", buys.index.tolist())
    if len(sells) > 0:
        print("Sell Dates:", sells.index.tolist())
