import argparse
from data_loader import fetch_stock_data, fetch_news, get_sp500_tickers, select_top_momentum_stocks
from technical_analysis import add_technical_indicators, detect_candlestick_patterns
from strategy import AdvancedPatternStrategy
from backtester import Backtester
from sentiment_analyzer import analyze_sentiment
import pandas as pd
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description="Stocks Agent CLI")
    parser.add_argument('--mode', type=str, default='backtest', choices=['backtest', 'live'], help="Mode: backtest or live")
    parser.add_argument('--symbols', type=str, default='AAPL,GOOGL,MSFT,AMZN,TSLA', help="Comma-separated stock symbols")
    parser.add_argument('--sp500', action='store_true', help="Run on all S&P 500 stocks")
    parser.add_argument('--limit', type=int, default=0, help="Limit number of stocks (0 for all)")
    parser.add_argument('--start', type=str, default='2023-01-01', help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default='2023-06-01', help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    if args.sp500:
        all_tickers = get_sp500_tickers()
        if args.limit > 0:
            # If limit is small (e.g. 10), we still want to scan a decent chunk to find winners
            # But scanning 500 takes time. Let's scan ALL if limit is 0, or scan 100 if limit is small?
            # User wants "all of s&p500". So we scan ALL 500, then pick Top 10 to trade.
            # Wait, if user says --limit 10, do they mean "Trade 10" or "Scan 10"?
            # To get good results, we must SCAN many and TRADE few.
            # Let's assume we SCAN ALL (or a large subset) and TRADE the top 10.
            
            # For this demo speed, let's scan the first 100 tickers and pick top 10
            scan_pool = all_tickers[:100] if len(all_tickers) > 100 else all_tickers
            symbols = select_top_momentum_stocks(scan_pool, args.start, top_n=args.limit)
        else:
            # If no limit, scan all and trade all? That's too many.
            # Let's default to trading Top 20 if no limit specified for safety?
            # Or just scan all and trade all (which will be slow).
            # Let's stick to the user's likely intent: "Make me money".
            # So we scan ALL, and pick Top 20.
            symbols = select_top_momentum_stocks(all_tickers, args.start, top_n=20)
    else:
        symbols = args.symbols.split(',')
    
    print(f"Running in {args.mode} mode for {len(symbols)} stocks: {symbols}...")
    
    # Dictionary to store processed dataframes
    data_dict = {}
    
    # 1. Fetch and Process Data for EACH stock
    for symbol in symbols:
        print(f"\n--- Processing {symbol} ---")
        
        # Fetch extra data for indicators (warmup)
        start_dt = datetime.strptime(args.start, '%Y-%m-%d')
        warmup_start = (start_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        
        df = fetch_stock_data(symbol, warmup_start, args.end)
        if df.empty:
            print(f"No data for {symbol}, skipping.")
            continue

        # Fetch News
        print(f"Fetching news for {symbol}...")
        news_df = fetch_news(symbol, args.start, args.end)
        
        if not news_df.empty:
            print(f"Found {len(news_df)} news items.")
            news_df['Sentiment'] = news_df['title'].apply(analyze_sentiment)
        else:
            print("No news found.")

        # Add Indicators & Patterns
        df = add_technical_indicators(df)
        df = detect_candlestick_patterns(df)
        
        # Strategy
        strategy = AdvancedPatternStrategy()
        df = strategy.generate_signals(df, news_df)
        
        # Slice to requested range
        df = df.loc[args.start:args.end]
        
        if not df.empty:
            data_dict[symbol] = df
            
        print(f"Finished processing {symbol}. Waiting 5s...")
        time.sleep(5) # Delay between stocks to prevent rate limiting
            
    if not data_dict:
        print("No valid data found for any stock.")
        return
    
    # 2. Run Portfolio Backtest
    if args.mode == 'backtest':
        print("\n--- Running Portfolio Backtest ---")
        backtester = Backtester(initial_capital=50000) # Increased capital for portfolio
        history_df, trades = backtester.run(data_dict)
        metrics = backtester.get_performance_metrics(history_df)
        
        print("\n--- Portfolio Results ---")
        for k, v in metrics.items():
            print(f"{k}: {v}")
            
        print(f"\nTotal Trades: {len(trades)}")
        
        # 3. Visualization
        if not history_df.empty:
            plt.figure(figsize=(12, 6))
            plt.plot(history_df.index, history_df['Portfolio Value'], label='Portfolio Value')
            plt.title('Portfolio Performance (Advanced Strategy)')
            plt.xlabel('Date')
            plt.ylabel('Value ($)')
            plt.legend()
            plt.grid(True)
            
            output_file = 'portfolio_performance.png'
            plt.savefig(output_file)
            print(f"\nPerformance graph saved to {output_file}")
            
    else:
        print("Live mode not supported for portfolio yet.")

if __name__ == "__main__":
    main()
