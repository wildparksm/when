#!/bin/bash
# Install dependencies for the collector
sudo apt-get update
pip3 install -r /home/azureuser/azure-functions-collection/requirements.txt
pip3 install feedparser requests markupsafe

# Remove any existing cron job for manual_trigger to prevent duplicates
crontab -l | grep -v "manual_trigger.py" | crontab -

# Add the new cron job to run every 30 minutes
(crontab -l 2>/dev/null; echo "*/30 * * * * cd /home/azureuser/azure-functions-collection && python3 manual_trigger.py >> /home/azureuser/collector.log 2>&1") | crontab -

echo 'Crontab configured successfully!'
crontab -l
