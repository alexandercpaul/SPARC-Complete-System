#!/usr/bin/env python3
"""Local SPARC - Build Instacart API Client with latency tracking"""
import sys
sys.path.insert(0, '/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System')

from local_sparc_instacart import LocalSPARC
from pathlib import Path
import time
import json

# Read spec
spec = Path("/tmp/instacart_api_client_spec.txt").read_text()

print("🚀 Starting Local SPARC for Instacart API Client")
print(f"   Spec: {len(spec)} chars")
print(f"   Started: {time.strftime('%H:%M:%S')}")
print()

start = time.time()
sparc = LocalSPARC()
# FIXED: Changed from run_sparc(spec) to run()
# Note: run() takes NO parameters and is hardcoded for voice parsing
result = sparc.run()
duration = time.time() - start

print()
print(f"✅ Local SPARC Complete!")
print(f"   Duration: {duration:.1f}s")
print(f"   Output: /tmp/instacart_api_client.json")

# Save with metadata
output = {
    "spec": spec,
    "result": result,
    "duration_seconds": duration,
    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
    "mode": "local_sparc"
}
Path("/tmp/instacart_api_client.json").write_text(json.dumps(output, indent=2))
