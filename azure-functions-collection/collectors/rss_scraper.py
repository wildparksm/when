import feedparser
import logging
from datetime import datetime
from dateutil import parser
import time

RSS_FEEDS = {
    "bloomberg_crypto": "https://feeds.bloomberg.com/crypto/news.rss",
    "reuters_business": "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best"
}

def fetch_rss_feeds(last_cursor_ts_ms):
    """
    Scrapes RSS feeds using feedparser.
    Converts published_parsed to ms timestamp to filter out old entries.
    """
    new_data = []
    latest_cursor = last_cursor_ts_ms

    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            
            # Feeds usually return newest first
            for entry in reversed(feed.entries):
                # Try to get published date
                pub_date_str = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
                if not pub_date_str:
                    continue
                    
                dt_obj = parser.isoparse(pub_date_str)
                article_ts_ms = dt_obj.timestamp() * 1000.0
                
                if article_ts_ms > last_cursor_ts_ms:
                    item = {
                        "source": source_name,
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published_at": pub_date_str,
                        "description": entry.get("summary", "")
                    }
                    new_data.append(item)
                    if article_ts_ms > latest_cursor:
                        latest_cursor = article_ts_ms

        except Exception as e:
            logging.error(f"Error fetching RSS from {source_name}: {e}")

    return new_data, latest_cursor
