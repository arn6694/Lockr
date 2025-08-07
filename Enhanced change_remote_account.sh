#!/bin/bash
# Enhanced change_remote_account.sh
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_characters> <username> <servername>"
  exit 1
fi

num_chars=$1
username=$2
servername=$3
current_date=$(date '+%Y-%m-%d_%H-%M-%S')

# Generate unique password (same Python code as before)
password=$(python3 - <<EOF
import random
import string
def generate_password(length):
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_characters = string.punctuation
    all_characters = uppercase_letters + lowercase_letters + digits + special_characters
    password = ''.join(random.choice(all_characters) for _ in range(length))
    return password
print(generate_password($num_chars))
EOF
)

# Hash the password
hashed_password=$(openssl passwd -6 "$password")

# Create vault structure with date
vault_dir="/home/svc_ans/playbooks/files/vault"
vault_file="${vault_dir}/${servername}_${username}_${current_date}"
metadata_file="${vault_dir}/${servername}_${username}_current"

mkdir -p "$vault_dir"

# Store password with metadata
cat > "$vault_file" <<EOF
server: $servername
username: $username
password: $password
created: $current_date
EOF

# Encrypt the file
ansible-vault encrypt "$vault_file" --vault-password-file /home/svc_ans/.vault_key

# Update current pointer (for easy retrieval)
echo "$vault_file" > "$metadata_file"

echo "Password for user $username on server $servername has been updated and stored in Ansible Vault"
echo "$hashed_password"
