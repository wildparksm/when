import subprocess
import os

print('1. Copying azure-functions-collection to B1s Control Tower...')
# Using SCP recursive
res_scp = subprocess.run(['scp', '-r', 'g:/doc/When/azure-functions-collection', 'control-tower:/home/azureuser/'])
if res_scp.returncode != 0:
    print('SCP Failed')

remote_setup = f'''#!/bin/bash
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
'''

with open('g:/doc/When/setup_cron.sh', 'w', newline='\n') as f:
    f.write(remote_setup)

print('2. Executing dependency installation and Crontab setup via SSH...')
subprocess.run(['scp', 'g:/doc/When/setup_cron.sh', 'control-tower:/tmp/setup_cron.sh'])
subprocess.run(['ssh', 'control-tower', 'bash', '/tmp/setup_cron.sh'])

print("Collector Deployment and Cron Setup Complete.")
