import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure lexicon is downloaded
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a text string.
    Returns a compound score between -1 (negative) and 1 (positive).
    """
    if not text:
        return 0.0
    
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(text)
    return scores['compound']

if __name__ == "__main__":
    print(f"Sentiment of 'I love this stock!': {analyze_sentiment('I love this stock!')}")
    print(f"Sentiment of 'This company is going bankrupt.': {analyze_sentiment('This company is going bankrupt.')}")
