# Gemini Workspace
Created: 2025-12-31 11:52:59

## Structure
- logs/ - API call logs, error logs
- outputs/ - Generated content, responses
- research/ - Research findings, web search results

## Usage
```python
from pathlib import Path
workspace = Path("/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/gemini-task-2025-12-31-1152")

# Write log
(workspace / "logs" / "task.log").write_text("Log message")

# Write output
(workspace / "outputs" / "result.json").write_text(json.dumps(data))

# Write research
(workspace / "research" / "findings.md").write_text("Research results")
```
