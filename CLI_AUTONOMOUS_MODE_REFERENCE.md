# CLI Autonomous Mode Reference (YOLO/Headless/Non-Interactive)
## Complete Guide for All 4 Installed CLIs

## 1. Claude CLI (Current Session - You!)
**Binary**: `/opt/homebrew/bin/claude`
**Autonomous flags**: Built-in Task tool with `run_in_background=true`
**Best for**: Strategic orchestration, architecture, complex reasoning
**Usage**:
```python
# Spawn background agents via Task tool
Task(
    subagent_type="general-purpose",
    prompt="Your task here",
    run_in_background=True,  # ← YOLO mode
    model="haiku"  # or "sonnet" or "opus"
)
```

## 2. Codex CLI (GPT/OpenAI)
**Binary**: `/opt/homebrew/bin/codex`
**Autonomous flags**:
- `--ask-for-approval never` - No approval prompts
- `--dangerously-bypass-approvals-and-sandbox` - Full YOLO mode
- `--full-auto` - Convenience alias
- `-a on-failure` - Only ask on failure
**Best for**: Code generation, implementation, technical writing
**Usage**:
```bash
# YOLO mode (background process with &)
codex exec "Write Python function for X" \
  --ask-for-approval never \
  --dangerously-bypass-approvals-and-sandbox \
  > /tmp/codex_agent_output.log 2>&1 &

# Get PID for monitoring
CODEX_PID=$!
echo $CODEX_PID > /tmp/codex_agent.pid
```

## 3. Gemini CLI (Google)
**Binary**: `/opt/homebrew/bin/gemini`
**Autonomous flags**:
- `-y` or `--yolo` - Auto-accept all actions
- `--approval-mode yolo` - Alternative syntax
- `--approval-mode auto_edit` - Auto-approve edit tools only
- `-p "prompt"` - Non-interactive mode with prompt
**Best for**: Research, web search, multimodal tasks
**Usage**:
```bash
# YOLO mode (background process with &)
gemini -p "Research topic X" \
  --yolo \
  > /tmp/gemini_agent_output.log 2>&1 &

# Alternative syntax
gemini "Research task" --approval-mode yolo &
```

## 4. QWEN/Ollama (Local - No Approval Needed!)
**Binary**: `/opt/homebrew/bin/ollama`
**Server**: `http://localhost:11434` (PID 84288 running)
**Models available**:
- `qwen2.5-coder:7b` - Best for code (S-tier performance)
- `llava:latest` - Multimodal (vision + text)
- `sparc-qwen:latest` - Custom SPARC-tuned model
**Best for**: Unlimited parallel agents, cost-free iteration
**Usage**:

### Option A: Direct API (Recommended for SPARC)
```bash
# Background inference via API
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5-coder:7b",
    "prompt": "Write Python code for X",
    "stream": false
  }' > /tmp/qwen_agent_13_output.json 2>&1 &

QWEN_PID=$!
```

### Option B: ollama run command
```bash
# Synchronous execution (use & for background)
ollama run qwen2.5-coder:7b "Generate code for X" \
  > /tmp/qwen_output.log 2>&1 &
```

## SPARC Phase 4 Multi-Agent Launch Strategy

**8 Agents Total**:
- 3 Claude Sonnet (Agents 15, 16, 18, 20) - Complex modules
- 5 QWEN (Agents 13, 14, 17, 19) - Code generation

**Launch Pattern**:
```bash
# 1. Launch all 5 QWEN agents simultaneously (unlimited, $0)
for agent in 13 14 17 19; do
  curl -X POST http://localhost:11434/api/generate \
    -d @/tmp/agent_${agent}_prompt.json \
    > /tmp/sparc_phase4_agent${agent}_output.json 2>&1 &
  echo $! > /tmp/agent_${agent}.pid
done

# 2. Launch 3 Claude agents via Task tool (in parallel)
# (Use Task tool with run_in_background=True for each)

# 3. Monitor all agents
watch -n 5 'ps -p $(cat /tmp/agent_*.pid 2>/dev/null | tr "\n" "," | sed "s/,$//") 2>/dev/null'
```

## Cost & Performance

| CLI | Cost | Speed | Limit | Use Case |
|-----|------|-------|-------|----------|
| **Claude** | $200/mo (unlimited via subscription) | Fast | Unlimited | Architecture, reasoning |
| **Codex** | $200/mo (unlimited via subscription) | Fast | Unlimited | Code implementation |
| **Gemini** | $250/mo (unlimited via subscription) | Fast | Unlimited | Research, web search |
| **Ollama** | **$0** (local) | Very fast | **Unlimited** | Parallel code gen |

**Key Insight**: Ollama = unlimited parallel agents at zero marginal cost!

## Monitoring Background Agents

```bash
# Check all running agents
ps aux | grep -E "(codex|gemini|ollama run|claude)" | grep -v grep

# Check Ollama API active models
curl -s http://localhost:11434/api/ps

# Tail agent outputs
tail -f /tmp/*agent*output.log
```

## Status
- ✅ Claude: Documented (Task tool)
- ✅ Codex: Documented (--ask-for-approval never)
- ✅ Gemini: Documented (--yolo / --approval-mode yolo)
- ✅ Ollama: Documented (API + run command)

## Created
2026-01-01 by Claude Sonnet 4.5 (COMPREHENSIVE EDITION)
