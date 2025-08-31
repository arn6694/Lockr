#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status

# This script runs on ser8 (central server) to set up SSH access on target servers
# It requires existing SSH access to the target server (password or key)

TARGET_SERVER="${1:-10.10.10.5}"
TARGET_HOSTNAME="${2:-checkmk}"
ADMIN_USER="brian"
SSH_KEY="AAAAC3NzaC1lZDI1NTE5AAAAIK2pqLwc4m7rYEtpvAnBJbfl+PBvxloHFGed7F38IHV8"
PUBKEY="ssh-ed25519 ${SSH_KEY} ${ADMIN_USER}@ser8"

echo "Setting up SSH access for ${TARGET_HOSTNAME} (${TARGET_SERVER})"

# Check if we can reach the target server
if ! ping -c 1 -W 3 "${TARGET_SERVER}" > /dev/null 2>&1; then
    echo "Error: Cannot reach target server ${TARGET_SERVER}"
    exit 1
fi

# Try to SSH to the target server and set up the user
# Note: This requires existing access (password or key)
echo "Attempting to set up SSH access on ${TARGET_SERVER}..."

# Create a temporary setup script to execute on the target server
TEMP_SCRIPT=$(mktemp)
cat > "${TEMP_SCRIPT}" << 'EOF'
#!/bin/bash
set -e

ADMIN_USER="brian"
SSH_KEY="AAAAC3NzaC1lZDI1NTE5AAAAIK2pqLwc4m7rYEtpvAnBJbfl+PBvxloHFGed7F38IHV8"
PUBKEY="ssh-ed25519 ${SSH_KEY} ${ADMIN_USER}@ser8"
HOME_DIR="/home/${ADMIN_USER}"
SUDOERS_FILE="/etc/sudoers.d/sudoers_${ADMIN_USER}"

echo "Setting up user ${ADMIN_USER} on $(hostname)..."

# Check if the user 'brian' exists; if not, create the user
if ! grep -q "^${ADMIN_USER}:" /etc/passwd; then
    echo "Creating local user ${ADMIN_USER}..."
    useradd -d "${HOME_DIR}" -m -s /bin/bash ${ADMIN_USER}
    passwd -l ${ADMIN_USER}
fi

# Ensure the .ssh directory exists for the user
if [ ! -d "${HOME_DIR}/.ssh" ]; then
    echo "Creating ${HOME_DIR}/.ssh directory..."
    mkdir -p "${HOME_DIR}/.ssh"
    chown -R ${ADMIN_USER}:${ADMIN_USER} "${HOME_DIR}"
    chmod 700 "${HOME_DIR}/.ssh"
fi  

# Path to the authorized_keys file
AUTHORIZED_KEYS="${HOME_DIR}/.ssh/authorized_keys"

# Add the public key if it is not already present
if [ ! -f "${AUTHORIZED_KEYS}" ] || ! grep -q "${SSH_KEY}" "${AUTHORIZED_KEYS}"; then
    echo "Adding public key to ${AUTHORIZED_KEYS}..."
    cat <<EOF2 >> "${AUTHORIZED_KEYS}"
${PUBKEY}
EOF2
    chown -R ${ADMIN_USER}:${ADMIN_USER} "${HOME_DIR}/.ssh"
    chmod 600 "${AUTHORIZED_KEYS}"
fi

# Grant passwordless sudo privileges to the user
if [ ! -f "${SUDOERS_FILE}" ]; then
    echo "Setting up sudo for ${ADMIN_USER}..."
    echo "${ADMIN_USER} ALL=(ALL) NOPASSWD: ALL" > "${SUDOERS_FILE}"
    chmod 644 "${SUDOERS_FILE}"
fi

echo "Setup completed successfully for user ${ADMIN_USER}"
EOF

# Try to execute the setup script on the target server
# This requires existing SSH access (you'll need to provide credentials)
echo "Executing setup script on ${TARGET_SERVER}..."
echo "Note: You may need to provide existing credentials for ${TARGET_SERVER}"

# Try to use ssh-copy-id to copy the SSH key to the existing brian user
echo "Attempting to copy SSH key using ssh-copy-id to existing brian user..."

# Copy the SSH key to the existing brian user
if ssh-copy-id -i ~/.ssh/id_ed25519.pub "brian@${TARGET_SERVER}"; then
    echo "SSH key copied to brian user successfully"
    
    # Test the new SSH key authentication
    echo "Testing new SSH access..."
    if ssh -i ~/.ssh/id_ed25519 "brian@${TARGET_SERVER}" "echo 'SSH key authentication working!'"; then
        echo "✅ SSH setup verified successfully!"
        echo ""
        echo "Note: The brian user on ${TARGET_SERVER} may not have sudo access without password."
        echo "This is normal and expected. SSH key authentication is now working."
        exit 0
    else
        echo "⚠️  SSH setup completed but verification failed"
        exit 1
    fi
else
    echo "❌ Failed to copy SSH key using ssh-copy-id"
    echo "You may need to set up SSH access manually or provide existing credentials"
    echo ""
    echo "Manual steps:"
    echo "1. SSH to ${TARGET_SERVER} as brian user"
    echo "2. Run: mkdir -p ~/.ssh"
    echo "3. Run: echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK2pqLwc4m7rYEtpvAnBJbfl+PBv8 brian@ser8' >> ~/.ssh/authorized_keys"
    echo "4. Run: chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
    exit 1
fi

# Clean up
rm -f "${TEMP_SCRIPT}"
