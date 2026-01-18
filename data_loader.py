import yfinance as yf
from GoogleNews import GoogleNews
import pandas as pd
from datetime import datetime, timedelta
import time

def fetch_stock_data(symbol, start_date, end_date):
    """
    Fetches historical stock data using yfinance.
    """
    print(f"Fetching stock data for {symbol} from {start_date} to {end_date}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)
    return df

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
        for i in range(1, 6): # Pages 1 to 5
            googlenews.getpage(i)
            page_results = googlenews.result()
            if page_results:
                results.extend(page_results)
            time.sleep(1) # Be nice to the server
            
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
