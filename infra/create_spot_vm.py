import subprocess
import os
import sys

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

# Read SSH key
key_path = os.path.expanduser('~/.ssh/dual_transformer_key.pub')
if not os.path.exists(key_path):
    print(f"Error: Public key not found at {key_path}")
    sys.exit(1)

with open(key_path, 'r', encoding='utf-8') as f:
    key_val = f.read().strip()

print("1. Creating Spot VM (Standard_NC4as_T4_v3)...")
cmd_create = [
    'az.cmd', 'vm', 'create',
    '--resource-group', 'DualTransformer_RG',
    '--name', 'ml-spot-vm',
    '--image', 'Ubuntu2204',
    '--size', 'Standard_NC4as_T4_v3',
    '--priority', 'Spot',
    '--eviction-policy', 'Deallocate',
    '--max-price', '-1',
    '--admin-username', 'azureuser',
    '--ssh-key-values', key_val,
    '--public-ip-sku', 'Standard'
]
res1 = subprocess.run(cmd_create, env=env, capture_output=True, text=True, errors='replace')
print("CREATE STDOUT:", res1.stdout)
print("CREATE STDERR:", res1.stderr)

if res1.returncode != 0:
    print("Failed to create VM. Exiting.")
    sys.exit(res1.returncode)

print("2. Retrieving Public IP...")
cmd_ip = [
    'az.cmd', 'vm', 'show', '-d', '-g', 'DualTransformer_RG', '-n', 'ml-spot-vm', '--query', 'publicIps', '-o', 'tsv'
]
res_ip = subprocess.run(cmd_ip, env=env, capture_output=True, text=True, errors='replace')
public_ip = res_ip.stdout.strip()
print(f"Spot VM Public IP: {public_ip}")

print("3. Installing NVIDIA GPU Extension (this may take a while)...")
cmd_ext = [
    'az.cmd', 'vm', 'extension', 'set',
    '--resource-group', 'DualTransformer_RG',
    '--vm-name', 'ml-spot-vm',
    '--name', 'NvidiaGpuDriverLinux',
    '--publisher', 'Microsoft.HpcCompute',
    '--version', '1.6'
]
res3 = subprocess.run(cmd_ext, env=env, capture_output=True, text=True, errors='replace')
print("EXT STDOUT:", res3.stdout)
print("EXT STDERR:", res3.stderr)

print("4. Updating local ~/.ssh/config...")
ssh_config_path = os.path.expanduser('~/.ssh/config')
config_entry = f"\nHost spot-gpu\n    HostName {public_ip}\n    User azureuser\n    IdentityFile ~/.ssh/dual_transformer_key\n    StrictHostKeyChecking no\n"

with open(ssh_config_path, 'a', encoding='utf-8') as f:
    f.write(config_entry)

print("All infrastructure setup completed successfully!")
