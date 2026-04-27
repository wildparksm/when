import os
import torch
import logging
from DualTransformer import Model as DualTransformerModel
from data_harness import LocalFileDataHarness, AzureBlobDataHarness
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)

def load_inference_model(blob_conn_str, container, filename="model_latest.pth"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DualTransformerModel(num_companies=13).to(device)
    model.eval()
    
    local_path = f"/tmp/{filename}"
    try:
        blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
        blob_client = blob_service.get_blob_client(container=container, blob=f"checkpoints/{filename}")
        
        if blob_client.exists():
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            checkpoint = torch.load(local_path, map_location=device)
            model.load_state_dict(checkpoint['model_state_dict'])
            logging.info(f"[Inference] Loaded checkpoint from Epoch {checkpoint['epoch']}")
        else:
            logging.warning("[Inference] No checkpoint found. Using untrained weights.")
    except Exception as e:
        logging.warning(f"[Inference] Blob storage error or not configured. Using untrained weights: {e}")
        
    return model, device

def run_inference():
    blob_conn_str = os.environ.get("AzureWebJobsStorage", "INSERT_YOUR_CONN_STR")
    
    # 1. Load Model
    model, device = load_inference_model(blob_conn_str, "raw-data")
    
    # 2. Fetch Latest Data for Prediction
    # Switch to AzureBlobDataHarness in prod
    harness = LocalFileDataHarness("./dataset")
    
    sentiment_data = harness.fetch_sentiment_data().to(device)
    prices_data, time_data = harness.fetch_price_data()
    prices_data = prices_data.to(device)
    time_data = time_data.to(device)
    
    # 3. Forward Pass (No gradients needed)
    with torch.no_grad():
        predictions = model(sentiment_data, prices_data, time_data)
    
    # The output shape is (Batch, num_companies) e.g., (16, 13)
    # Take the last batch element as the most recent prediction
    latest_preds = predictions[-1].cpu().numpy()
    
    logging.info(f"[Inference] Generated predictions for {len(latest_preds)} companies.")
    return latest_preds

if __name__ == "__main__":
    preds = run_inference()
    print("Raw Output Scores:", preds)
