import subprocess
import os
import keyring
from getpass import getpass
from datetime import datetime, timedelta

# Constants
KEYCHAIN_SERVICE = "1Password CLI"
TOKEN_KEY = "session_token"
EXPIRY_KEY = "expiry_time"

def get_keychain_value(key):
    return keyring.get_password(KEYCHAIN_SERVICE, key)

def set_keychain_value(key, value):
    keyring.set_password(KEYCHAIN_SERVICE, key, value)

def delete_keychain_value(key):
    keyring.delete_password(KEYCHAIN_SERVICE, key)

def is_token_valid():
    expiry_time_str = get_keychain_value(EXPIRY_KEY)
    if not expiry_time_str:
        return False
    expiry_time = datetime.fromisoformat(expiry_time_str)
    return datetime.now() < expiry_time

def get_session_token():
    if is_token_valid():
        return get_keychain_value(TOKEN_KEY)

    print("Session token expired. Please enter your 1Password master password to generate a new one.")
    master_password = getpass(prompt="Enter 1Password master password: ")
    
    try:
        result = subprocess.run(
            ["op", "signin", "--account", "your_account_name"],
            input=master_password.encode(),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Failed to sign in:", result.stderr)
            return None
        
        token = result.stdout.strip()
        expiry_time = datetime.now() + timedelta(hours=1)  # Token expires after 1 hour

        set_keychain_value(TOKEN_KEY, token)
        set_keychain_value(EXPIRY_KEY, expiry_time.isoformat())
        
        print("Session token generated and cached.")
        return token
    except Exception as e:
        print(f"Error generating session token: {e}")
        return None

def run_op_command(command):
    token = get_session_token()
    if not token:
        print("Failed to get session token. Exiting.")
        return 1
    
    try:
        result = subprocess.run(
            ["op"] + command,
            env={"OP_SESSION": token},
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Command failed:", result.stderr)
            return result.returncode
        
        print(result.stdout)
        return 0
    except Exception as e:
        print(f"Error running command: {e}")
        return 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="1Password CLI wrapper without prompts")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="1Password CLI command to run")
    
    args = parser.parse_args()
    
    if not args.command:
        print("No command provided. Use --help for usage.")
        return 1
    
    return run_op_command(args.command)

if __name__ == "__main__":
    exit(main())
