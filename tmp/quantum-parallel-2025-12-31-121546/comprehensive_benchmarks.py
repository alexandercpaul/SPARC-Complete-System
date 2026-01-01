
import subprocess
import time
import json
from datetime import datetime

models = [
    "qwen2.5-coder:7b",
    "sparc-qwen",
    "llama3.2:latest",
    "conductor-sparc"
]

results = {
    "timestamp": datetime.now().isoformat(),
    "benchmarks": {}
}

test_prompt = "Write a Python function to calculate fibonacci sequence recursively and iteratively"

for model in models:
    print(f"\n{'='*60}")
    print(f"Benchmarking: {model}")
    print('='*60)
    
    try:
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model, test_prompt],
            capture_output=True,
            timeout=45,
            text=True
        )
        elapsed = time.time() - start
        
        results["benchmarks"][model] = {
            "time_seconds": round(elapsed, 2),
            "output_length": len(result.stdout),
            "success": result.returncode == 0,
            "chars_per_second": round(len(result.stdout) / elapsed, 1) if elapsed > 0 else 0
        }
        
        print(f"✅ {model}:")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Output: {len(result.stdout)} chars")
        print(f"   Speed: {len(result.stdout)/elapsed:.1f} chars/sec")
        
    except Exception as e:
        print(f"❌ {model}: {e}")
        results["benchmarks"][model] = {"error": str(e)}

print(f"\n\n{'='*60}")
print("FINAL RESULTS:")
print('='*60)
print(json.dumps(results, indent=2))
