# Lockr SSH Setup via Ansible

This directory contains the Ansible playbook system for automatically setting up SSH access on new servers.

## How It Works

1. **Lockr identifies** a server that needs SSH setup
2. **Lockr executes** the `setup_server_ssh.sh` script
3. **Script runs** Ansible playbook on central server (10.10.10.96)
4. **Central server executes** `brian-install.sh` for the target server
5. **SSH access** is configured automatically

## Files

- **`setup_ssh_access.yml`** - Main Ansible playbook
- **`inventory_central.yml`** - Inventory for central server
- **`setup_server_ssh.sh`** - Wrapper script (in parent directory)

## Prerequisites

### On Central Server (10.10.10.96):
- `brian-install.sh` script exists at `/home/brian/brian-install.sh`
- User `brian` has sudo access
- SSH key authentication is set up

### On Lockr Server:
- Ansible is installed (`sudo apt install ansible`)
- SSH key can reach central server (10.10.10.96)

## Usage

### From Lockr Dashboard:
1. Click "Retry SSH Setup" on a server with "setup_required" status
2. Lockr automatically executes the Ansible playbook
3. Check the result in the dashboard

### From Command Line:
```bash
# Setup SSH for a specific server
./setup_server_ssh.sh 10.10.10.5 checkmk

# Setup SSH with defaults (10.10.10.5, checkmk)
./setup_server_ssh.sh
```

## What the Playbook Does

1. **Connects to central server** (10.10.10.96)
2. **Verifies** `brian-install.sh` exists
3. **Executes** the script with target server parameters
4. **Reports** success/failure back to Lockr

## Troubleshooting

### Common Issues:
- **Central server unreachable**: Check SSH access to 10.10.10.96
- **Script not found**: Ensure `brian-install.sh` exists on central server
- **Permission denied**: Verify `brian` user has sudo access on central server

### Manual Setup:
If Ansible setup fails, you can manually:
1. SSH to the target server using existing credentials
2. Add your SSH public key to `~/.ssh/authorized_keys`
3. Test SSH key authentication
4. Use "Test Connection" in Lockr to verify

## Security Notes

- The playbook runs with your SSH key authentication
- Only executes on servers you control
- Uses sudo on central server (requires proper permissions)
- Scripts are executed in your user context
