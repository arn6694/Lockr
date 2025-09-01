#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status

# Custom parameters for the brian account
ADMIN_USER="brian"
SSH_KEY="AAAAC3NzaC1lZDI1NTE5AAAAIK2pqLwc4m7rYEtpvAnBJbfl+PBvxloHFGed7F38IHV8"
PUBKEY="ssh-ed25519 ${SSH_KEY} ${ADMIN_USER}@ser8"
HOME_DIR="/home/${ADMIN_USER}"
SUDOERS_FILE="/etc/sudoers.d/sudoers_${ADMIN_USER}"

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
    cat <<EOF >> "${AUTHORIZED_KEYS}"
${PUBKEY}
EOF
    chown -R ${ADMIN_USER}:${ADMIN_USER} "${HOME_DIR}/.ssh"
    chmod 600 "${AUTHORIZED_KEYS}"
fi

# Grant passwordless sudo privileges to the user
if [ ! -f "${SUDOERS_FILE}" ]; then
    echo "Setting up sudo for ${ADMIN_USER}..."
    echo "${ADMIN_USER} ALL=(ALL) NOPASSWD: ALL" > "${SUDOERS_FILE}"
    chmod 644 "${SUDOERS_FILE}"
fi

