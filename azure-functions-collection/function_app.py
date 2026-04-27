import azure.functions as func
import logging
from datetime import datetime, timezone
import os

from utils.cursor_manager import get_blob_service_client, get_last_cursor, save_cursor, upload_data_to_blob
from collectors.cryptocompare_api import fetch_cryptocompare_data
from collectors.rss_scraper import fetch_rss_feeds

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */30 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def dual_transformer_data_collector(myTimer: func.TimerRequest) -> None:
    now_utc = datetime.now(timezone.utc)
    
    if myTimer.past_due:
        logging.warning("The timer is past due! Catch-up collection triggered.")

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
    except Exception as e:
        logging.error(f"CryptoCompare collector failed: {e}")

    # --- 2. RSS Collection (Reuters, Bloomberg, etc) ---
    try:
        rss_cursor = get_last_cursor(blob_service, "rss")
        rss_data, rss_new_cursor = fetch_rss_feeds(rss_cursor)
        if rss_data:
            upload_data_to_blob(blob_service, rss_data, "rss_news", now_utc)
            save_cursor(blob_service, "rss", rss_new_cursor)
    except Exception as e:
        logging.error(f"RSS collector failed: {e}")

    logging.info("Dual Transformer data collection cycle finished successfully.")
