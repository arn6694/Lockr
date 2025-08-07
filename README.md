Usage Examples:
bash# List all stored passwords
./retrieve_password.sh -l

# Get root password for server01
./retrieve_password.sh -s server01

# Get backup user password for server02
./retrieve_password.sh -s server02 -u backup

# Show password history for server01
./retrieve_password.sh -h server01
