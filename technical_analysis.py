import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands

def add_technical_indicators(df):
    """
    Adds technical indicators to the dataframe.
    """
    df = df.copy()
    
    # SMA
    df['SMA_20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    df['SMA_50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    
    # RSI
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    
    # MACD
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Bollinger Bands
    bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    
    # Stochastic Oscillator
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    return df

def detect_candlestick_patterns(df):
    """
    Detects simple candlestick patterns.
    """
    df = df.copy()
    
    # Bullish Engulfing
    # Previous candle red, Current candle green
    # Current Open < Prev Close AND Current Close > Prev Open
    df['Bullish_Engulfing'] = (
        (df['Close'].shift(1) < df['Open'].shift(1)) & # Prev Red
        (df['Close'] > df['Open']) & # Curr Green
        (df['Open'] < df['Close'].shift(1)) & # Open lower than prev close
        (df['Close'] > df['Open'].shift(1))   # Close higher than prev open
    )
    
    # Hammer
    # Small body, long lower wick, short/no upper wick
    # (High - Low) > 3 * (Open - Close) (Body is small)
    # (Close - Low) / (.001 + High - Low) > 0.6 (Long lower wick)
    # (High - Close) / (.001 + High - Low) < 0.1 (Small upper wick)
    # Green Hammer: Close > Open
    body = (df['Close'] - df['Open']).abs()
    range_len = df['High'] - df['Low']
    lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
    upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
    
    df['Hammer'] = (
        (lower_wick > 2 * body) & 
        (upper_wick < body)
    )
    
    return df

if __name__ == "__main__":
    # Mock data for testing
    data = {'Close': [100, 101, 102, 103, 102, 101, 100, 99, 98, 99, 100, 102, 105, 108, 110]}
    df = pd.DataFrame(data)
    df = add_technical_indicators(df)
    print(df)
