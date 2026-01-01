# Ollama Workspace
Created: 2025-12-31 11:52:59
Date: 2025-12-31 (all Ollama runs for this date share this workspace)

## Structure
- logs/ - Ollama server logs, model logs
- outputs/ - Generated code, responses
- model-outputs/ - Per-model outputs
  - qwen2.5-coder/ - Code generation outputs
  - sparc-qwen/ - SPARC planning outputs
  - llama3.2/ - Fast generation outputs
  - conductor-sparc/ - Orchestration outputs

## Usage
```python
from pathlib import Path
workspace = Path("/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/ollama-runs-2025-12-31")

# Write log
(workspace / "logs" / "ollama_server.log").write_text("Server log")

# Write output
(workspace / "outputs" / "response.txt").write_text(response)

# Write model-specific output
model = "qwen2.5-coder"
(workspace / "model-outputs" / model / f"output_{timestamp}.txt").write_text(output)
```
