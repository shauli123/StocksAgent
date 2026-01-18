import pandas as pd
import numpy as np

class BaseStrategy:
    def generate_signals(self, df, news_df=None):
        raise NotImplementedError

class AdvancedPatternStrategy(BaseStrategy):
    def generate_signals(self, df, news_df=None):
        """
        Generates signals based on a multi-factor scoring system.
        """
        df = df.copy()
        df['Signal'] = 0
        df['Score'] = 0
        
        # 1. Trend (SMA Crossover / Alignment)
        # +2 if SMA 20 > SMA 50 (Uptrend) - Increased weight to capture trends earlier
        df.loc[df['SMA_20'] > df['SMA_50'], 'Score'] += 2
        
        # 2. Momentum (RSI)
        # +2 if RSI < 30 (Oversold - Reversal Buy)
        # -2 if RSI > 70 (Overbought - Reversal Sell)
        df.loc[df['RSI'] < 30, 'Score'] += 2
        df.loc[df['RSI'] > 70, 'Score'] -= 2
        
        # 3. Momentum (MACD)
        # +1 if MACD > Signal (Bullish Momentum)
        df.loc[df['MACD'] > df['MACD_Signal'], 'Score'] += 1
        
        # 4. Volatility (Bollinger Bands)
        # +2 if Close < BB_Low (Oversold/Dip Buy)
        df.loc[df['Close'] < df['BB_Low'], 'Score'] += 2
        
        # 5. Candlestick Patterns
        # +2 for Bullish Engulfing
        # +1 for Hammer
        if 'Bullish_Engulfing' in df.columns:
            df.loc[df['Bullish_Engulfing'], 'Score'] += 2
        if 'Hammer' in df.columns:
            df.loc[df['Hammer'], 'Score'] += 1
            
        # Sentiment Integration
        if news_df is not None and not news_df.empty:
            print("Applying sentiment filter...")
            daily_sentiment = news_df.groupby('Date')['Sentiment'].mean()
            df['Sentiment'] = df.index.map(daily_sentiment)
            df['Sentiment'] = df['Sentiment'].fillna(method='ffill').fillna(0)
            
            # +2 for Positive Sentiment, -2 for Negative
            df.loc[df['Sentiment'] > 0.1, 'Score'] += 2
            df.loc[df['Sentiment'] < -0.1, 'Score'] -= 2

        # Decision Threshold
        # Buy if Score >= 3 (Moderate Confluence - tuned for earlier entry)
        # Sell if Score <= 0 (Weakness)
        
        df.loc[df['Score'] >= 3, 'Signal'] = 1
        df.loc[df['Score'] <= 0, 'Signal'] = -1
        
        # Force Sell on Death Cross (Trend Reversal)
        death_cross = (df['SMA_20'] < df['SMA_50']) & (df['SMA_20'].shift(1) >= df['SMA_50'].shift(1))
        df.loc[death_cross, 'Signal'] = -1
        
        return df
