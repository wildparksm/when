import os
import torch
import torch.nn as nn
from torch.amp import autocast, GradScaler
from data_harness import LocalFileDataHarness, AzureBlobDataHarness
from azure.storage.blob import BlobServiceClient
import logging

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. Spot Checkpointing & Resume Management
# ==========================================
def save_checkpoint(model, optimizer, epoch, blob_conn_str, container, filename="model_latest.pth"):
    local_path = f"/tmp/{filename}"
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, local_path)
    
    try:
        blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
        blob_client = blob_service.get_blob_client(container=container, blob=f"checkpoints/{filename}")
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        logging.info(f"[SpotSafe] Checkpoint saved locally and synced to Blob Storage at Epoch {epoch}")
    except Exception as e:
        logging.error(f"[SpotSafe] Failed to sync checkpoint to Blob: {e}")

def load_checkpoint(model, optimizer, blob_conn_str, container, filename="model_latest.pth"):
    local_path = f"/tmp/{filename}"
    try:
        blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
        blob_client = blob_service.get_blob_client(container=container, blob=f"checkpoints/{filename}")
        
        if blob_client.exists():
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            checkpoint = torch.load(local_path)
            model.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            logging.info(f"[SpotSafe] Resumed training safely from Epoch {checkpoint['epoch']}")
            return checkpoint['epoch']
        else:
            logging.info("[SpotSafe] No checkpoint found. Starting fresh.")
            return 0
    except Exception as e:
        logging.warning(f"[SpotSafe] Error checking blob for checkpoint. Starting fresh. ({e})")
        return 0

# ==========================================
# 2. Main Training Loop & Mixed Precision
# ==========================================
def train_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f"Using Device: {device}")
    
    # Here you'd switch to AzureBlobDataHarness in prod
    harness = LocalFileDataHarness("./dataset")
    
    # Load the real Dual Transformer Architecture
    from DualTransformer import DualTransformerAIModel

    model = DualTransformerAIModel(news_dim=768, price_dim=7, d_model=64, num_companies=13).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Mixed Precision Setup for T4 Tensor Cores (16GB handling)
    scaler = GradScaler()
    
    blob_conn_str = os.environ.get("AzureWebJobsStorage", "INSERT_YOUR_CONN_STR")
    
    # Check Spot-Eviction Resume State
    start_epoch = load_checkpoint(model, optimizer, blob_conn_str, "raw-data")
    
    epochs = 100
    for epoch in range(start_epoch, epochs):
        # Data Bridge: load dynamically
        news_data = harness.fetch_news_sentiment_data().to(device)
        prices_data = harness.fetch_price_data().to(device)
        
        optimizer.zero_grad()
        
        # Mixed Precision Forward & Backward
        with autocast('cuda' if 'cuda' in str(device) else 'cpu'):
            # Dual Transformer forward pass
            output = model(news_data, prices_data)
            # True label would be next step price changes. Dummy zero label for testing.
            target = torch.zeros_like(output).to(device)
            loss = torch.mean((output - target) ** 2)
            
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        logging.info(f"Epoch {epoch+1}/{epochs} | Loss: {loss.item():.4f}")
        
        # Save Spot Safe Checkpoint every 10 epochs (or based on time)
        if (epoch + 1) % 10 == 0:
            save_checkpoint(model, optimizer, epoch + 1, blob_conn_str, "raw-data")

if __name__ == "__main__":
    train_model()
