import requests
import os
import logging
from datetime import datetime

def fetch_cryptocompare_data(last_cursor_ts_ms):
    """
    Fetches news from CryptoCompare API.
    API Key is expected to be in CRYPTOCOMPARE_API_KEY env block.
    """
    api_key = os.environ.get("CRYPTOCOMPARE_API_KEY", "")
    if not api_key:
        logging.warning("CRYPTOCOMPARE_API_KEY not found. Skipping CryptoCompare collection.")
        return [], last_cursor_ts_ms
        
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    headers = {
        "authorization": f"Apikey {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        articles = data.get("Data", [])
    except Exception as e:
        logging.error(f"Error fetching CryptoCompare data: {e}")
        return [], last_cursor_ts_ms

    new_data = []
    latest_cursor = last_cursor_ts_ms

    # CryptoCompare returns articles ordered by latest first.
    # We iterate reversed so we process oldest to newest within the pagination.
    for article in reversed(articles):
        # 'published_on' is in Unix epoch seconds
        pub_sec = article.get("published_on")
        if not pub_sec:
            continue
            
        article_ts_ms = float(pub_sec) * 1000.0
        
        # Cursor logic: deduplication
        if article_ts_ms > last_cursor_ts_ms:
            new_data.append(article)
            if article_ts_ms > latest_cursor:
                latest_cursor = article_ts_ms
                
    return new_data, latest_cursor
