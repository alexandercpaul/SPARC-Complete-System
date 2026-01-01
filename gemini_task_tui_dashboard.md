# GEMINI TASK: Build System Monitoring TUI Dashboard

## Priority: HIGH - User explicitly requested this

## Background
User has disability/typing difficulty and needs a real-time TUI dashboard to monitor the entire multi-agent system without constant manual checking.

## Requirements

### 1. Technology Stack
- **Language**: Python (user-friendly, good TUI libraries)
- **TUI Library**: `rich` or `textual` (both support animations, streaming updates)
- **Data Sources**: Process monitoring, file watching, log tailing

### 2. Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ MULTI-AGENT SYSTEM MONITOR                    [00:12:45]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ HIERARCHY:                                                   │
│ ┌──Claude (CEO)──────────────────────────────────┐         │
│ │  Status: Active | Token: 79823/200000 (40%)    │         │
│ │  Task: Strategic oversight                      │         │
│ └────┬────────────────────────────────────────────┘         │
│      │                                                       │
│      ├──Codex (Manager)───────────────────────────┐        │
│      │   Status: Active | PID: 609                 │        │
│      │   Task: Instacart automation                │        │
│      │   Last Output: 5min ago                     │        │
│      └─────┬───────────────────────────────────────┘        │
│            │                                                 │
│            ├──Gemini CLI (Coordinator)────────────┐        │
│            │   Status: Active                      │        │
│            │   Task: Managing 2x2 Ollama workers   │        │
│            └─────┬─────────────────────────────────┘        │
│                  │                                           │
│                  ├──Team A───────────────────────┐         │
│                  │  ├─Worker A1 (llava) PID:27268│         │
│                  │  │  Status: IDLE (Hello loop) │         │
│                  │  │  Uptime: 1727s             │         │
│                  │  └─Worker A2 (llava) PID:27315│         │
│                  │     Status: IDLE (Hello loop) │         │
│                  │     Uptime: 1727s             │         │
│                  │                                          │
│                  └──Team B───────────────────────┐         │
│                     ├─Worker B1 (llava) PID:27350│         │
│                     │  Status: IDLE (Hello loop) │         │
│                     │  Uptime: 1727s             │         │
│                     └─Worker B2 (llava) PID:27394│         │
│                        Status: IDLE (Hello loop) │         │
│                        Uptime: 1727s             │         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ RECENT ACTIVITY:                                            │
│ [02:15:43] Codex: Captured add_to_cart GraphQL hash        │
│ [02:15:44] Codex: FAILED view_cart - no operations         │
│ [02:15:45] Gemini: Reported cart navigation failure        │
│ [02:16:00] Ollama-A1: Drift detected - idle responses      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ ARTIFACTS & LOGS:                                           │
│ Codex: /tmp/instacart_graphql_hashes_v2.json [75 ops]      │
│ Gemini: ~/.gemini/tmp/.../chats/session-*.json             │
│ Ollama: ~/.gemini/tmp/.../ollama_workers/*/output.log      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3. Core Features

**Data Collection:**
- Monitor processes: `ps aux | grep -E "(codex|gemini|ollama)"`
- Watch log files: `tail -f ~/.gemini/tmp/*/ollama_workers/*/output.log`
- Track artifacts: `ls -lh /tmp/*.json`
- Monitor Claude context: Parse current conversation for token usage

**Real-Time Updates:**
- Refresh every 2 seconds (configurable)
- Streaming log tail in activity section
- Animated spinners for active processes
- Color coding: Green (active), Yellow (idle), Red (error)

**Animations:**
- Pulse effect on active agents
- Scroll activity log from bottom
- Progress bars for long-running tasks
- Status indicator animations

**Drift Detection:**
- Pattern match Ollama outputs for "Hello!" idle responses
- Alert when worker hasn't produced meaningful output in 5min
- Highlight drifted agents in RED

### 4. Implementation Plan

**Phase 1: Basic Layout (30min)**
- Create Python script with `textual` framework
- Build static layout with panels for hierarchy, activity, artifacts
- Test rendering

**Phase 2: Data Collection (45min)**
- Write process monitoring functions
- Implement log file tailing
- Parse JSON artifacts
- Test data flow

**Phase 3: Live Updates (30min)**
- Set up 2-second refresh loop
- Stream activity log
- Update process statuses

**Phase 4: Animations & Polish (45min)**
- Add status indicators with animations
- Color coding based on agent state
- Drift detection highlighting
- Error alerts

**Total Time: ~2.5 hours**

### 5. Deliverables

1. **File**: `/tmp/system_monitor_dashboard.py` - Main dashboard script
2. **File**: `/tmp/dashboard_config.json` - Configuration (refresh rate, colors, etc.)
3. **File**: `/tmp/DASHBOARD_README.md` - Usage instructions
4. **Test**: Run dashboard and verify all 8 Ollama workers show correctly
5. **Test**: Verify drift detection highlights idle workers

### 6. Success Criteria

- [ ] Dashboard displays full agent hierarchy (Claude → Codex → Gemini → 2x2 Ollama)
- [ ] Real-time updates every 2 seconds
- [ ] Activity log shows last 10 events
- [ ] Artifacts section lists relevant files
- [ ] Drift detection works (highlights "Hello!" idle workers)
- [ ] Animations render smoothly
- [ ] User can run with single command: `python3 /tmp/system_monitor_dashboard.py`

## Why This Matters

User needs this dashboard because:
1. Disability makes constant manual checking difficult
2. Multi-agent system complex - hard to track without visualization
3. Drift detection prevents agents from wasting resources
4. Real-time monitoring enables quick intervention

## Ollama Sub-Delegation

Gemini: You can delegate to your 2x2 Ollama workers:
- **Team A Workers**: Handle data collection (process monitoring, log parsing)
- **Team B Workers**: Handle rendering (layout generation, color coding)

Use the workers that are currently idle!

---

**IMPORTANT**: This is the user's TOP priority system monitoring tool. Build it properly and make it beautiful.
