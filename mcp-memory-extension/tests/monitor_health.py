#!/usr/bin/env python3
"""
Continuous Health Monitor for MCP Memory + 30TB Integration
Checks server health every 5 minutes and logs status
"""
import requests
import time
import json
from datetime import datetime
from pathlib import Path
import sys

# Configuration
BASE_URL = "http://127.0.0.1:3000"
CHECK_INTERVAL = 300  # 5 minutes in seconds
LOG_FILE = Path.home() / ".mcp-memory" / "health_monitor.log"

def log_message(message):
    """Log message to file and stdout"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"

    print(log_entry)

    # Ensure log directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)

    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

def check_health():
    """Check server health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "timestamp": datetime.now().isoformat()
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "error": "Connection refused",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_vector_store_size():
    """Get current vector store size"""
    vector_store = Path.home() / ".mcp-memory" / "vector_store.pkl"
    if vector_store.exists():
        size = vector_store.stat().st_size
        return {
            "exists": True,
            "size_bytes": size,
            "size_kb": size / 1024,
            "path": str(vector_store)
        }
    else:
        return {
            "exists": False,
            "path": str(vector_store)
        }

def monitor(continuous=True, count=None):
    """Run health monitoring"""
    log_message("Starting MCP Memory Health Monitor")
    log_message(f"Check interval: {CHECK_INTERVAL} seconds")
    log_message(f"Server endpoint: {BASE_URL}")
    log_message(f"Log file: {LOG_FILE}")
    log_message("-" * 80)

    checks = 0
    while True:
        checks += 1

        # Check health
        health = check_health()
        store = get_vector_store_size()

        # Format status message
        if health["status"] == "healthy":
            message = f"✅ HEALTHY | Server: {health['data'].get('service', 'N/A')} | Store: {store.get('size_kb', 0):.2f} KB"
        elif health["status"] == "offline":
            message = f"❌ OFFLINE | {health.get('error', 'Unknown error')}"
        elif health["status"] == "unhealthy":
            message = f"⚠️ UNHEALTHY | {health.get('error', 'Unknown error')}"
        else:
            message = f"⚠️ ERROR | {health.get('error', 'Unknown error')}"

        log_message(message)

        # Exit if count reached
        if count is not None and checks >= count:
            log_message(f"Completed {checks} health checks")
            break

        # Exit if not continuous
        if not continuous:
            break

        # Wait for next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor MCP Memory server health")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Check health once and exit"
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Number of checks to perform before exiting"
    )

    args = parser.parse_args()

    try:
        if args.once:
            monitor(continuous=False)
        else:
            monitor(continuous=True, count=args.count)
    except KeyboardInterrupt:
        log_message("Monitor stopped by user")
        sys.exit(0)
