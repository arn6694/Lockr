#!/bin/bash
# Check if the number of characters is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_characters> <username> <servername>"
  exit 1
fi
num_chars=$1
username=$2
servername=$3
# Python code to generate the password
password=$(python3 - <<EOF
import random
import string
def generate_password(length):
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_characters = string.punctuation
    all_characters = uppercase_letters + lowercase_letters + digits + special_characters
    password = ''.join(random.choice(allcharacters) for  in range(length))
    return password
print(generate_password($num_chars))
EOF
)
# Hash the generated password using openssl
hashed_password=$(openssl passwd -6 "$password")
# Output the generated and hashed passwords
echo "Generated Password: $password"
#echo "Hashed Password: $hashed_password"
# Define the vault file path
vault_dir="/home/svc_ans/playbooks/files/vault"
vault_file="${vaultdir}/${servername}${username}_password"
# Ensure the vault directory exists
mkdir -p "$vault_dir"
# Store the password in a plaintext file
echo "$password" > "$vault_file"
# Encrypt the plaintext file using Ansible Vault
ansible-vault encrypt "$vault_file" --vault-password-file /home/svc_ans/.vault_key
echo "Password for user $username on server $servername has been updated and stored in Ansible Vault at $vault_file"
# Return the hashed password
echo "$hashed_password"
