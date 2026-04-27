import os
import json
import logging
from datetime import datetime, timezone
import sys

# Change working directory so utils/collectors can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cursor_manager import get_blob_service_client, get_last_cursor, save_cursor, upload_data_to_blob
from collectors.cryptocompare_api import fetch_cryptocompare_data
from collectors.rss_scraper import fetch_rss_feeds

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def manual_run():
    logging.info("Starting Manual Data Collection (Bypassing 'func start')...")
    
    # Load settings manually to mimic Azure env
    try:
        with open('local.settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        os.environ['AzureWebJobsStorage'] = settings['Values']['AzureWebJobsStorage']
        os.environ['CRYPTOCOMPARE_API_KEY'] = settings['Values'].get('CRYPTOCOMPARE_API_KEY', '')
    except Exception as e:
        logging.error(f"Failed to load local.settings.json: {e}")
        return

    now_utc = datetime.now(timezone.utc)
    
    try:
        blob_service = get_blob_service_client()
    except Exception as e:
        logging.error(f"Failed to connect to Azure Blob Storage: {e}")
        return
        
    # --- 1. CryptoCompare Collection ---
    try:
        cc_cursor = get_last_cursor(blob_service, "cryptocompare")
        cc_data, cc_new_cursor = fetch_cryptocompare_data(cc_cursor)
        if cc_data:
            upload_data_to_blob(blob_service, cc_data, "cryptocompare", now_utc)
            save_cursor(blob_service, "cryptocompare", cc_new_cursor)
            logging.info(f"CryptoCompare: {len(cc_data)} items collected.")
        else:
            logging.info("CryptoCompare: No new items.")
    except Exception as e:
        logging.error(f"CryptoCompare collector failed: {e}")

    # --- 2. RSS Collection ---
    try:
        rss_cursor = get_last_cursor(blob_service, "rss")
        rss_data, rss_new_cursor = fetch_rss_feeds(rss_cursor)
        if rss_data:
            upload_data_to_blob(blob_service, rss_data, "rss", now_utc)
            save_cursor(blob_service, "rss", rss_new_cursor)
            logging.info(f"RSS: {len(rss_data)} items collected.")
        else:
            logging.info("RSS: No new items.")
    except Exception as e:
        logging.error(f"RSS collector failed: {e}")
        
    logging.info("Manual Data Collection Run Complete! The data is now in Azure Blob Storage.")

if __name__ == "__main__":
    manual_run()
