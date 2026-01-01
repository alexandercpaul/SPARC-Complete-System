# Codex Workspace
Created: 2025-12-31 11:52:59

## Structure
- logs/ - Cloud task logs, API logs
- outputs/ - Generated code, test results
- code-executions/ - Code run in cloud sandbox

## Usage
```python
from pathlib import Path
workspace = Path("/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/codex-task-2025-12-31-1152")

# Write log
(workspace / "logs" / "cloud_task.log").write_text("Task log")

# Write code output
(workspace / "outputs" / "generated_code.py").write_text(code)

# Write execution result
(workspace / "code-executions" / "run_result.json").write_text(json.dumps(result))
```
