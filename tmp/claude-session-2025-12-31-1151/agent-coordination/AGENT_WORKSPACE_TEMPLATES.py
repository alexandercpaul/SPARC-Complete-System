#!/usr/bin/env python3
"""
Agent Workspace Templates
Copy-paste code for each agent type to create organized workspaces
"""
from pathlib import Path
from datetime import datetime
import json

# Base path for all agent workspaces
BASE_PATH = Path("/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp")

def create_gemini_workspace():
    """Create organized workspace for Gemini agents"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    workspace = BASE_PATH / f"gemini-task-{timestamp}"

    # Create structure
    (workspace / "logs").mkdir(parents=True, exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)
    (workspace / "research").mkdir(exist_ok=True)

    # Save workspace path for easy access
    Path("/tmp/gemini_workspace_path.txt").write_text(str(workspace))

    # Create README
    (workspace / "README.md").write_text(f"""# Gemini Workspace
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
- logs/ - API call logs, error logs
- outputs/ - Generated content, responses
- research/ - Research findings, web search results

## Usage
```python
from pathlib import Path
workspace = Path("{workspace}")

# Write log
(workspace / "logs" / "task.log").write_text("Log message")

# Write output
(workspace / "outputs" / "result.json").write_text(json.dumps(data))

# Write research
(workspace / "research" / "findings.md").write_text("Research results")
```
""")

    return workspace

def create_codex_workspace():
    """Create organized workspace for Codex agents"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    workspace = BASE_PATH / f"codex-task-{timestamp}"

    # Create structure
    (workspace / "logs").mkdir(parents=True, exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)
    (workspace / "code-executions").mkdir(exist_ok=True)

    # Save workspace path
    Path("/tmp/codex_workspace_path.txt").write_text(str(workspace))

    # Create README
    (workspace / "README.md").write_text(f"""# Codex Workspace
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
- logs/ - Cloud task logs, API logs
- outputs/ - Generated code, test results
- code-executions/ - Code run in cloud sandbox

## Usage
```python
from pathlib import Path
workspace = Path("{workspace}")

# Write log
(workspace / "logs" / "cloud_task.log").write_text("Task log")

# Write code output
(workspace / "outputs" / "generated_code.py").write_text(code)

# Write execution result
(workspace / "code-executions" / "run_result.json").write_text(json.dumps(result))
```
""")

    return workspace

def create_ollama_workspace():
    """Create organized workspace for Ollama agents (date-based, shared)"""
    date = datetime.now().strftime("%Y-%m-%d")
    workspace = BASE_PATH / f"ollama-runs-{date}"

    # Create structure
    (workspace / "logs").mkdir(parents=True, exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)
    (workspace / "model-outputs").mkdir(exist_ok=True)
    (workspace / "model-outputs" / "qwen2.5-coder").mkdir(exist_ok=True)
    (workspace / "model-outputs" / "sparc-qwen").mkdir(exist_ok=True)
    (workspace / "model-outputs" / "llama3.2").mkdir(exist_ok=True)
    (workspace / "model-outputs" / "conductor-sparc").mkdir(exist_ok=True)

    # Save workspace path
    Path("/tmp/ollama_workspace_path.txt").write_text(str(workspace))

    # Create README
    (workspace / "README.md").write_text(f"""# Ollama Workspace
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Date: {date} (all Ollama runs for this date share this workspace)

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
workspace = Path("{workspace}")

# Write log
(workspace / "logs" / "ollama_server.log").write_text("Server log")

# Write output
(workspace / "outputs" / "response.txt").write_text(response)

# Write model-specific output
model = "qwen2.5-coder"
(workspace / "model-outputs" / model / f"output_{{timestamp}}.txt").write_text(output)
```
""")

    return workspace

def get_or_create_workspace(agent_type):
    """Get existing workspace or create new one"""
    workspace_file = f"/tmp/{agent_type}_workspace_path.txt"

    if Path(workspace_file).exists():
        workspace_path = Path(Path(workspace_file).read_text().strip())
        if workspace_path.exists():
            return workspace_path

    # Create new workspace
    if agent_type == "gemini":
        return create_gemini_workspace()
    elif agent_type == "codex":
        return create_codex_workspace()
    elif agent_type == "ollama":
        return create_ollama_workspace()
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

# Example usage for each agent type
if __name__ == "__main__":
    print("🗂️ Agent Workspace Templates")
    print("=" * 80)
    print()

    # Example: Create Gemini workspace
    print("Example: Creating Gemini workspace...")
    gemini_ws = create_gemini_workspace()
    print(f"✅ Created: {gemini_ws}")
    print()

    # Example: Create Codex workspace
    print("Example: Creating Codex workspace...")
    codex_ws = create_codex_workspace()
    print(f"✅ Created: {codex_ws}")
    print()

    # Example: Create Ollama workspace
    print("Example: Creating Ollama workspace...")
    ollama_ws = create_ollama_workspace()
    print(f"✅ Created: {ollama_ws}")
    print()

    print("=" * 80)
    print("All workspaces created!")
    print()
    print("Workspace paths saved to:")
    print("  /tmp/gemini_workspace_path.txt")
    print("  /tmp/codex_workspace_path.txt")
    print("  /tmp/ollama_workspace_path.txt")
