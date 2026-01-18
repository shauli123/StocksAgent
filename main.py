import argparse
from data_loader import fetch_stock_data, fetch_news
from technical_analysis import add_technical_indicators, detect_candlestick_patterns
from strategy import AdvancedPatternStrategy
from backtester import Backtester
from sentiment_analyzer import analyze_sentiment
import pandas as pd
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description="Stocks Agent CLI")
    parser.add_argument('--mode', type=str, default='backtest', choices=['backtest', 'live'], help="Mode: backtest or live")
    parser.add_argument('--symbol', type=str, default='AAPL', help="Stock symbol")
    parser.add_argument('--start', type=str, default='2023-01-01', help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default='2023-06-01', help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    print(f"Running in {args.mode} mode for {args.symbol}...")
    
    # 1. Fetch Data
    # Fetch extra data for indicators (warmup)
    start_dt = datetime.strptime(args.start, '%Y-%m-%d')
    warmup_start = (start_dt - timedelta(days=90)).strftime('%Y-%m-%d')
    
    df = fetch_stock_data(args.symbol, warmup_start, args.end)
    if df.empty:
        print("No stock data found.")
        return

    # 2. Fetch News
    print("Fetching news for sentiment analysis...")
    news_df = fetch_news(args.symbol, args.start, args.end)
    
    if not news_df.empty:
        print(f"Found {len(news_df)} news items. Analyzing sentiment...")
        news_df['Sentiment'] = news_df['title'].apply(analyze_sentiment)
        print(f"Average Sentiment: {news_df['Sentiment'].mean()}")
    else:
        print("No news found or news fetching failed. Proceeding without sentiment.")

    # 3. Add Indicators & Patterns
    df = add_technical_indicators(df)
    df = detect_candlestick_patterns(df)
    
    # 4. Strategy
    strategy = AdvancedPatternStrategy()
    df = strategy.generate_signals(df, news_df)
    
    # Slice back to requested range
    df = df.loc[args.start:args.end]
    
    # 5. Backtest
    if args.mode == 'backtest':
        backtester = Backtester()
        result_df, trades = backtester.run(df)
        metrics = backtester.get_performance_metrics()
        
        print("\n--- Backtest Results ---")
        for k, v in metrics.items():
            print(f"{k}: {v}")
            
        print(f"\nTotal Trades: {len(trades)}")
        if len(trades) > 0:
            print("Last 5 Trades:")
            for t in trades[-5:]:
                print(t)
    else:
        print("Live mode not fully implemented yet.")

if __name__ == "__main__":
    main()
