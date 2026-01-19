import yfinance as yf
from GoogleNews import GoogleNews
import pandas as pd
from datetime import datetime, timedelta
import time
import random
from io import StringIO
import requests

def get_sp500_tickers():
    """
    Fetches the list of S&P 500 tickers from Wikipedia.
    """
    print("Fetching S&P 500 tickers from Wikipedia...")
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        table = pd.read_html(StringIO(response.text))
        df = table[0]
        tickers = df['Symbol'].tolist()
        # Clean tickers (e.g. BRK.B -> BRK-B for yfinance)
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return []

def select_top_momentum_stocks(tickers, reference_date, top_n=10):
    """
    Selects the top N stocks based on 6-month momentum prior to reference_date.
    """
    print(f"Scanning {len(tickers)} stocks for top {top_n} momentum winners...")
    
    end_date = datetime.strptime(reference_date, '%Y-%m-%d')
    start_date = end_date - timedelta(days=180) # 6 months lookback
    
    try:
        # Bulk download is faster
        # yfinance expects space-separated string
        tickers_str = " ".join(tickers)
        data = yf.download(tickers_str, start=start_date, end=end_date, progress=True)['Close']
        
        # Calculate Return: (End Price - Start Price) / Start Price
        # We use the first valid index and the last valid index for each column
        returns = {}
        
        for ticker in tickers:
            if ticker in data.columns:
                series = data[ticker].dropna()
                if not series.empty:
                    start_price = series.iloc[0]
                    end_price = series.iloc[-1]
                    if start_price > 0:
                        ret = (end_price - start_price) / start_price
                        returns[ticker] = ret
        
        # Sort by return descending
        sorted_tickers = sorted(returns.items(), key=lambda x: x[1], reverse=True)
        top_tickers = [t[0] for t in sorted_tickers[:top_n]]
        
        print(f"Top {top_n} Momentum Stocks: {top_tickers}")
        return top_tickers
        
    except Exception as e:
        print(f"Error in momentum selection: {e}")
        return tickers[:top_n] # Fallback

def fetch_stock_data(symbol, start_date, end_date):
    """
    Fetches historical stock data using direct Yahoo Finance API call.
    More robust for Vercel/Serverless environments.
    """
    print(f"Fetching stock data for {symbol} from {start_date} to {end_date}...")
    try:
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={start_ts}&period2={end_ts}&interval=1d&events=history&includeAdjustedClose=true"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()

def fetch_news(symbol, start_date, end_date):
    """
    Fetches news headlines for a given symbol within a date range.
    """
    print(f"Fetching news for {symbol}...")
    googlenews = GoogleNews()
    googlenews.set_lang('en')
    googlenews.set_encode('utf-8')
    
    # GoogleNews requires date format MM/DD/YYYY
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        googlenews.set_time_range(start_dt.strftime('%m/%d/%Y'), end_dt.strftime('%m/%d/%Y'))
        googlenews.search(symbol)
        
        # Fetch a few pages to get a sample of news
        results = []
        for i in range(1, 2): # Just 1 page to avoid 429 Rate Limiting
            try:
                googlenews.getpage(i)
                page_results = googlenews.result()
                if page_results:
                    results.extend(page_results)
                time.sleep(random.uniform(2, 4)) 
            except Exception as e:
                print(f"Warning: Could not fetch news page {i}: {e}")
                break
            
        if not results:
            print("No news found.")
            return pd.DataFrame()

        news_df = pd.DataFrame(results)
        
        # Clean up and parse dates
        # GoogleNews 'datetime' field is often None for older news, 'date' is a string
        # We will try to use 'datetime' if available, otherwise parse 'date'
        
        def parse_google_date(row):
            if isinstance(row.get('datetime'), datetime):
                return row['datetime']
            # Fallback for 'date' string is hard because it can be relative ("1 day ago") or absolute
            # For historical search, it's usually absolute e.g. "Jan 1, 2023"
            # But parsing it reliably is tough without dateparser. 
            # We will rely on the 'datetime' field which GoogleNews populates for recent/specific searches often.
            return row.get('datetime')

        news_df['Date'] = news_df.apply(parse_google_date, axis=1)
        news_df = news_df.dropna(subset=['Date'])
        
        if news_df.empty:
             print("Could not parse dates for news items.")
             return pd.DataFrame()

        news_df['Date'] = pd.to_datetime(news_df['Date']).dt.normalize() # Remove time component
        return news_df[['Date', 'title']]

    except Exception as e:
        print(f"Error fetching news: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test
    stock = fetch_stock_data("AAPL", "2023-01-01", "2023-01-10")
    print("Stock Data Head:")
    print(stock.head())
