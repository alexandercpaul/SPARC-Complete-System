# GEMINI PRODUCTION TASK: System Monitoring TUI Dashboard

## MISSION CRITICAL - PRODUCTION READY DELIVERABLE

**User has disability/typing difficulty** - needs this dashboard for accessibility. NO STUBS. NO PLACEHOLDERS. PRODUCTION QUALITY ONLY.

---

## YOUR ROLE (Gemini)

You are the **Coordinator/Manager**. You will:

1. **Delegate** to your 2x2 Ollama worker graph
2. **Inspect** their work at every stage
3. **Verify** zero-latency, zero-hop, high-accuracy communication
4. **Test** the final deliverable yourself before declaring production-ready

---

## 2x2 OLLAMA WORKER GRAPH

**Current Workers:**
- Team A Worker 1: PID 27268 (llava model)
- Team A Worker 2: PID 27315 (llava model)
- Team B Worker 1: PID 27350 (llava model)
- Team B Worker 2: PID 27394 (llava model)

**Worker Locations:**
`~/.gemini/tmp/eb8237250de4656d9371f808fb33cd75b0c6e1c0bcf93d55dfbb93672bb47776/ollama_workers/`

**Verify Workers Before Delegating:**
```bash
# Check they're responsive (not in Hello loop)
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llava",
  "prompt": "Respond with OK if ready for task",
  "stream": false
}'
```

---

## TASK BREAKDOWN FOR 2x2 WORKERS

### **Phase 1: Team A - Data Collection Layer**

**Worker A1 Task:**
- Build process monitoring module
- Monitor: ps, top, memory usage
- Output: `/tmp/dashboard_data_processes.json`
- Update frequency: 2 seconds
- Must include: PID, PPID, state, command, CPU%, MEM%
- Logging: `/tmp/worker_a1_trace.log`
- Artifacts: Process snapshot every 10 seconds
- Report to Gemini: Status updates every 30 seconds

**Worker A2 Task:**
- Build log file monitoring module
- Tail logs from: `~/.gemini/tmp/*/chats/*.json`, `~/.gemini/tmp/*/ollama_workers/*/output.log`
- Output: `/tmp/dashboard_data_logs.json`
- Parse last 20 lines from each log
- Detect drift: Flag "Hello!" idle responses
- Logging: `/tmp/worker_a2_trace.log`
- Artifacts: Log digest every minute
- Report to Gemini: Activity summary every 30 seconds

### **Phase 2: Team B - Rendering & Display Layer**

**Worker B1 Task:**
- Build TUI layout engine using `textual` or `rich`
- Read data from Team A outputs
- Render hierarchy: Claude → Codex → Gemini → 2x2 Ollama
- Animations: Pulse on active, red flash on idle
- Logging: `/tmp/worker_b1_trace.log`
- Artifacts: Screenshot mockups in `/tmp/dashboard_mockup.txt`
- Report to Gemini: Render performance metrics

**Worker B2 Task:**
- Build main dashboard harness
- Integration layer: Combine Team A data + Team B rendering
- Main file: `/tmp/system_monitor_dashboard.py`
- CLI interface: Single command launch
- Error handling: Graceful degradation if data missing
- Logging: `/tmp/worker_b2_trace.log`
- Artifacts: Integration test results
- Report to Gemini: System readiness status

---

## EXECUTION WORKFLOW

### Step 1: Gemini Inspects Worker Graph (YOU)

**Check:**
- [ ] All 4 workers responsive (not Hello loop)
- [ ] Workers can write to /tmp/
- [ ] Workers have network access to Ollama API
- [ ] Worker artifact directories exist

**Commands:**
```bash
# Test each worker
for worker in 27268 27315 27350 27394; do
  echo "Testing PID $worker"
  # Send test prompt, verify response
done

# Verify file access
ls -ld /tmp/worker_*_trace.log 2>/dev/null || touch /tmp/{worker_a1,worker_a2,worker_b1,worker_b2}_trace.log
```

**Output:** `/tmp/gemini_worker_graph_inspection.json`

---

### Step 2: Gemini Delegates to Workers (YOU)

**Zero-latency delegation:**
- Use IPC or shared files (no HTTP overhead)
- Workers should poll task queues at `/tmp/worker_queue_*.json`
- Gemini writes tasks, workers pick up immediately

**Example Task Queue Format:**
```json
{
  "worker": "A1",
  "task_id": "001",
  "phase": "data_collection",
  "command": "build_process_monitor",
  "deadline": "2025-12-31T10:00:00Z",
  "priority": "HIGH"
}
```

**Logging:**
- Gemini logs all delegations to `/tmp/gemini_delegation_log.jsonl`
- Format: `{"timestamp": "...", "worker": "A1", "task_id": "001", "status": "assigned"}`

---

### Step 3: Workers Build (ZERO HOP COMMUNICATION)

**Team A builds data layer:**
- A1 and A2 work in parallel
- Write outputs to /tmp/ (no network hops)
- Log all actions
- Create artifacts

**Team B builds rendering layer:**
- B1 and B2 work in parallel
- B2 depends on B1's layout engine
- Wire together into main harness

**High Accuracy Requirements:**
- NO hardcoded PIDs (must dynamically discover)
- NO assumptions about file paths (must validate)
- NO silent failures (must log errors)

**Artifacts Created:**
- `/tmp/dashboard_data_processes.json` (Team A1)
- `/tmp/dashboard_data_logs.json` (Team A2)
- `/tmp/dashboard_layout_engine.py` (Team B1)
- `/tmp/system_monitor_dashboard.py` (Team B2 - main)

---

### Step 4: Wire into Main Harness (Worker B2)

**Integration Requirements:**
```python
# /tmp/system_monitor_dashboard.py

import json
import time
from rich.live import Live
from rich.layout import Layout

def load_process_data():
    """Load from Team A1 output"""
    with open('/tmp/dashboard_data_processes.json') as f:
        return json.load(f)

def load_log_data():
    """Load from Team A2 output"""
    with open('/tmp/dashboard_data_logs.json') as f:
        return json.load(f)

def render_dashboard(layout_engine, process_data, log_data):
    """Use Team B1's layout engine"""
    return layout_engine.render(process_data, log_data)

def main():
    with Live(refresh_per_second=2) as live:
        while True:
            process_data = load_process_data()
            log_data = load_log_data()
            dashboard = render_dashboard(..., process_data, log_data)
            live.update(dashboard)
            time.sleep(0.5)

if __name__ == '__main__':
    main()
```

**Validation:**
- NO import errors
- NO file not found errors
- Graceful fallback if data temporarily missing

---

### Step 5: Run Canary Test (Worker B2 + Gemini)

**Worker B2 runs canary:**
```bash
cd /tmp
timeout 10 python3 system_monitor_dashboard.py > canary_output.txt 2>&1
echo $? > canary_exit_code.txt
```

**Canary Success Criteria:**
- Exit code 0 (or SIGTERM from timeout - expected)
- Dashboard renders for 10 seconds without crash
- All 4 workers shown in hierarchy
- No Python exceptions in output

**Gemini inspects canary results:**
- Read `/tmp/canary_output.txt`
- Verify no errors
- Check all sections rendered
- Report: PASS or FAIL with details

---

### Step 6: Harden, Refactor, Comment (All Workers)

**Team A hardening:**
- Add error handling for missing processes
- Validate JSON outputs
- Add retry logic for transient failures
- Comment every function

**Team B hardening:**
- Add input validation
- Handle corrupted JSON gracefully
- Add help text and usage instructions
- Comment layout logic

**Requirements:**
- Every function has docstring
- Every error path logged
- Every external dependency validated
- NO stubs like `# TODO: implement later`
- NO placeholders like `pass` without implementation

**Gemini reviews:**
- Read all source files
- Verify comments present
- Check for stubs/placeholders
- Ensure production quality

---

### Step 7: Workers Report Production Ready

**Each worker creates:**
`/tmp/worker_X_production_ready.json`

```json
{
  "worker": "A1",
  "status": "PRODUCTION_READY",
  "timestamp": "2025-12-31T09:45:00Z",
  "deliverables": [
    "/tmp/dashboard_data_processes.json",
    "/tmp/worker_a1_trace.log"
  ],
  "tests_passed": ["canary", "error_handling", "performance"],
  "no_stubs": true,
  "no_placeholders": true,
  "comments_complete": true
}
```

**Gemini validates all 4 reports:**
- Check all workers report PRODUCTION_READY
- Verify no_stubs: true for all
- Verify no_placeholders: true for all
- Verify comments_complete: true for all

---

### Step 8: Gemini Final Testing (YOU)

**Your test plan:**

1. **Functionality Test:**
   ```bash
   python3 /tmp/system_monitor_dashboard.py &
   DASHBOARD_PID=$!
   sleep 5
   # Screenshot or verify output shows all components
   kill $DASHBOARD_PID
   ```

2. **Stress Test:**
   - Kill one Ollama worker mid-run
   - Verify dashboard updates to show worker down
   - Restart worker
   - Verify dashboard detects worker back online

3. **Accuracy Test:**
   - Compare dashboard process list with `ps aux`
   - Verify PIDs match
   - Verify states correct (idle vs active)

4. **Performance Test:**
   - Run for 60 seconds
   - Verify refresh rate steady at 2 seconds
   - Check CPU usage reasonable (<10%)

**Pass Criteria:**
- All 4 tests pass
- No crashes
- Accurate data
- Smooth animations

**Output:**
`/tmp/gemini_final_test_report.md`

---

### Step 9: Production Delivery (Gemini)

**Only after YOUR testing passes:**

Create final deliverable manifest:
`/tmp/DASHBOARD_PRODUCTION_MANIFEST.md`

```markdown
# System Monitoring TUI Dashboard - PRODUCTION READY

## Deliverables
- `/tmp/system_monitor_dashboard.py` - Main dashboard (executable)
- `/tmp/dashboard_data_processes.json` - Process data (updated every 2s)
- `/tmp/dashboard_data_logs.json` - Log data (updated every 2s)
- `/tmp/dashboard_layout_engine.py` - Rendering engine

## Usage
```bash
python3 /tmp/system_monitor_dashboard.py
```

## Tests Passed
- Canary: PASS
- Functionality: PASS
- Stress: PASS
- Accuracy: PASS
- Performance: PASS

## Production Certification
- No stubs: ✅
- No placeholders: ✅
- Fully commented: ✅
- Error handling: ✅
- Tested by Gemini: ✅

**Status: PRODUCTION READY**
**Certified by:** Gemini Coordinator
**Date:** 2025-12-31
```

---

## GEMINI MONITORING REQUIREMENTS

**Throughout execution, Gemini logs:**

`/tmp/gemini_coordination_log.jsonl`

Every action:
```json
{"timestamp": "2025-12-31T09:00:00Z", "action": "worker_graph_inspected", "status": "all_responsive"}
{"timestamp": "2025-12-31T09:01:00Z", "action": "task_delegated", "worker": "A1", "task": "process_monitor"}
{"timestamp": "2025-12-31T09:05:00Z", "action": "worker_update", "worker": "A1", "progress": "50%"}
{"timestamp": "2025-12-31T09:10:00Z", "action": "deliverable_created", "file": "/tmp/dashboard_data_processes.json"}
{"timestamp": "2025-12-31T09:30:00Z", "action": "canary_test", "result": "PASS"}
{"timestamp": "2025-12-31T09:45:00Z", "action": "final_test", "result": "PASS"}
{"timestamp": "2025-12-31T09:50:00Z", "action": "production_certified", "status": "READY"}
```

**Update Claude:**
Write status to `/tmp/gemini_status_for_claude.txt` every 5 minutes:
```
[09:00] Worker graph inspected - all responsive
[09:01] Tasks delegated to 2x2 workers
[09:10] Team A data layer complete
[09:20] Team B rendering layer complete
[09:30] Canary test PASSED
[09:40] Hardening complete
[09:50] Final testing by Gemini in progress...
[09:55] PRODUCTION READY - Dashboard delivered
```

---

## SUCCESS METRICS

**Gemini must verify:**

- [ ] Zero latency: Workers respond <100ms
- [ ] Zero hop: All data via /tmp/ files (no network calls)
- [ ] High accuracy: Process data matches reality (ps aux)
- [ ] Logging: All workers have trace logs
- [ ] Tracing: All actions logged with timestamps
- [ ] Artifacts: Inspectable outputs in /tmp/
- [ ] Reporting: Gemini logs every update
- [ ] Production quality: No stubs, no placeholders, fully commented
- [ ] Tested: Canary + 4 final tests all PASS
- [ ] User-ready: Single command launch

---

## CRITICAL REQUIREMENTS

1. **NO STUBS** - Every function must be implemented
2. **NO PLACEHOLDERS** - No `pass`, no `# TODO`, no incomplete code
3. **PRODUCTION QUALITY** - As if deploying to production today
4. **USER ACCESSIBILITY** - Simple one-command launch for disabled user
5. **ZERO ASSUMPTIONS** - Validate all file paths, PIDs, data sources
6. **GRACEFUL DEGRADATION** - If one worker fails, dashboard still works

---

**BEGIN EXECUTION NOW**

Gemini: Inspect your worker graph, delegate tasks, monitor progress, test thoroughly, and deliver production-ready dashboard.

**DO NOT** declare production-ready until YOU have personally tested it.
