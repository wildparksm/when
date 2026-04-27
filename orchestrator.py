import os
import time
import subprocess
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient

# Azure Configuration
BLOB_CONN_STR = os.environ.get("AzureWebJobsStorage", "INSERT_YOUR_CONN_STR")
CONTAINER_NAME = "raw-data"
RG_NAME = "DualTransformer_RG"
VM_NAME = "ml-spot-vm"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def count_new_data():
    """Dummy logic to count newly collected blob files."""
    try:
        blob_service = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
        container_client = blob_service.get_container_client(CONTAINER_NAME)
        # In a real scenario, you'd check blobs modified since last_training_run
        # For orchestrator layout, we just count today's blobs
        today_prefix = datetime.now().strftime("%Y/%m/%d")
        blobs = list(container_client.list_blobs(name_starts_with=today_prefix))
        return len(blobs)
    except Exception as e:
        logging.error(f"Blob connection failed: {e}")
        return 0

def run_spot_pipeline():
    logging.info("====================================")
    logging.info("Starting Spot VM to process data...")
    logging.info("====================================")
    
    # 1. Start VM
    subprocess.run(['az', 'vm', 'start', '-g', RG_NAME, '-n', VM_NAME], check=False)
    
    logging.info("Spot VM is Running. Dispatching Training Harness via Run-Command...")
    # 2. Execute Training Script via Azure Run-Command (Synchronous Wait)
    # Assuming code is synced via CI/CD into /home/azureuser/when
    cmd_run = [
        'az', 'vm', 'run-command', 'invoke',
        '-g', RG_NAME, '-n', VM_NAME,
        '--command-id', 'RunShellScript',
        '--scripts', 'source ~/.bashrc && cd /home/azureuser/when && git pull origin main && python3 train_harness.py'
    ]
    res = subprocess.run(cmd_run, capture_output=True, text=True)
    logging.info(f"Run-command Output: {res.stdout}")
    if res.returncode != 0:
        logging.error(f"Training Failed! STDERR: {res.stderr}")
        
    # 3. Deallocate VM immediately to cut costs to ZERO
    logging.info("====================================")
    logging.info("Training Run Complete. Deallocating Spot VM immediately...")
    logging.info("====================================")
    subprocess.run(['az', 'vm', 'deallocate', '-g', RG_NAME, '-n', VM_NAME], check=False)
    logging.info("Spot VM is Deallocated. Pipeline resting.")

def main():
    while True:
        data_count = count_new_data()
        logging.info(f"Current blob data count for today: {data_count}")
        
        # Condition: if more than 5 new data chunks have been aggregated
        if data_count >= 5:
            run_spot_pipeline()
            # Sleep for a long period to accumulate more before next run, e.g., 24 hours
            logging.info("Sleeping 24 hours until next lifecycle...")
            time.sleep(24 * 3600)
        else:
            logging.info("Insufficient data for training. Checking again in 30 minutes...")
            time.sleep(30 * 60)

if __name__ == "__main__":
    main()
