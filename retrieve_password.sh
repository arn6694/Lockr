#!/bin/bash
# retrieve_password.sh

VAULT_DIR="/home/svc_ans/playbooks/files/vault"
VAULT_KEY="/home/svc_ans/.vault_key"

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -s SERVER    Retrieve password for specific server"
    echo "  -u USERNAME  Specify username (default: root)"
    echo "  -l           List all available passwords"
    echo "  -h HOSTNAME  Show password history for hostname"
    echo "  --help       Show this help message"
}

list_passwords() {
    echo "Available password files:"
    echo "Server,Username,Date"
    for file in "$VAULT_DIR"/*_current; do
        if [ -f "$file" ]; then
            current_file=$(cat "$file")
            if [ -f "$current_file" ]; then
                # Extract info from filename
                basename_file=$(basename "$current_file")
                server=$(echo "$basename_file" | cut -d'_' -f1)
                username=$(echo "$basename_file" | cut -d'_' -f2)
                date=$(echo "$basename_file" | cut -d'_' -f3- | sed 's/_/ /g')
                echo "$server,$username,$date"
            fi
        fi
    done
}

get_password() {
    local server=$1
    local username=${2:-root}
    
    current_file="$VAULT_DIR/${server}_${username}_current"
    
    if [ ! -f "$current_file" ]; then
        echo "Error: No password found for $username@$server"
        return 1
    fi
    
    vault_file=$(cat "$current_file")
    
    if [ ! -f "$vault_file" ]; then
        echo "Error: Vault file not found: $vault_file"
        return 1
    fi
    
    echo "Retrieving password for $username@$server:"
    ansible-vault decrypt "$vault_file" --vault-password-file "$VAULT_KEY" --output=-
}

show_history() {
    local hostname=$1
    echo "Password history for $hostname:"
    ls -la "$VAULT_DIR"/${hostname}_*_20* 2>/dev/null | while read line; do
        file=$(echo "$line" | awk '{print $NF}')
        basename_file=$(basename "$file")
        username=$(echo "$basename_file" | cut -d'_' -f2)
        date=$(echo "$basename_file" | cut -d'_' -f3- | sed 's/_/ /g')
        echo "  $username: $date"
    done
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--server)
            SERVER="$2"
            shift 2
            ;;
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -l|--list)
            LIST=true
            shift
            ;;
        -h|--history)
            HISTORY="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute based on options
if [ "$LIST" = true ]; then
    list_passwords
elif [ -n "$HISTORY" ]; then
    show_history "$HISTORY"
elif [ -n "$SERVER" ]; then
    get_password "$SERVER" "$USERNAME"
else
    show_usage
fi
