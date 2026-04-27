import os
import json
import logging
from datetime import datetime, timezone, timedelta
from azure.storage.blob import BlobServiceClient

BLOB_CONN_STR = os.environ.get("AzureWebJobsStorage", "")
CONTAINER_NAME = "raw-data"

def get_blob_service_client():
    if not BLOB_CONN_STR:
        raise ValueError("AzureWebJobsStorage is not configured.")
    return BlobServiceClient.from_connection_string(BLOB_CONN_STR)

def get_last_cursor(blob_service_client, source_name):
    """
    Returns the last timestamp (in milliseconds) the collector successfully fetched.
    Fallback is 1 hour ago if no cursor exists.
    """
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"cursors/{source_name}_cursor.json")
        download_stream = blob_client.download_blob()
        data = json.loads(download_stream.readall())
        return float(data.get("last_timestamp"))
    except Exception as e:
        logging.warning(f"Cursor for {source_name} not found or error. Defaulting to 1 hour ago. ({e})")
        return (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp() * 1000.0

def save_cursor(blob_service_client, source_name, last_timestamp):
    """Saves the latest successful timestamp."""
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"cursors/{source_name}_cursor.json")
    blob_client.upload_blob(json.dumps({"last_timestamp": last_timestamp}), overwrite=True)

def upload_data_to_blob(blob_service_client, data, source_name, now_utc):
    """Uploads the JSON list to the target directory."""
    folder_path = now_utc.strftime("%Y/%m/%d/%H")
    file_name = f"{source_name}_{now_utc.strftime('%M%S')}.json"
    
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{folder_path}/{file_name}")
    blob_client.upload_blob(json.dumps(data, ensure_ascii=False, indent=2), overwrite=True)
    logging.info(f"[{source_name}] Saved {len(data)} records to {folder_path}/{file_name}")
