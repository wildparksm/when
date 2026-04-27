import json
import os
import subprocess

try:
    with open('g:/doc/When/azure-functions-collection/local.settings.json', 'r') as f:
        settings = json.load(f)
    conn_str = settings['Values']['AzureWebJobsStorage']
except Exception as e:
    print("Cannot read connection string:", e)
    conn_str = "DefaultEndpointsProtocol=https..."

print('1. Copying orchestrator.py to B1s Control Tower...')
subprocess.run(['scp', 'g:/doc/When/orchestrator.py', 'control-tower:/home/azureuser/orchestrator.py'])

remote_setup = f'''#!/bin/bash
sudo apt-get update && sudo apt-get install -y python3-pip
pip3 install azure-storage-blob
cat << 'EOF' > /home/azureuser/run_orchestrator.sh
#!/bin/bash
export AzureWebJobsStorage="{conn_str}"
nohup python3 /home/azureuser/orchestrator.py > /home/azureuser/orchestrator.log 2>&1 &
EOF
chmod +x /home/azureuser/run_orchestrator.sh
/home/azureuser/run_orchestrator.sh
echo 'Daemon successfully started. Logs are tailing in ~/orchestrator.log'
'''

with open('g:/doc/When/start_daemon.sh', 'w', newline='\n') as f:
    f.write(remote_setup)

print('2. Executing setup and daemon launch via SSH...')
# SCP the bash script over and run it
subprocess.run(['scp', 'g:/doc/When/start_daemon.sh', 'control-tower:/tmp/start_daemon.sh'])
subprocess.run(['ssh', 'control-tower', 'bash', '/tmp/start_daemon.sh'])

print("Deployment Complete.")
