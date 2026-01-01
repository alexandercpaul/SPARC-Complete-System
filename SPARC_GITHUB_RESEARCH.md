# SPARC Methodology: Official GitHub Research

## What is SPARC?

**SPARC** = **Specification → Pseudocode → Architecture → Refinement → Completion**

Systematic 5-phase framework for robust, scalable application development with focus on multi-agent AI collaboration.

## The 5 Phases

1. **Specification**: Requirements, user scenarios, acceptance criteria
2. **Pseudocode**: High-level logic roadmaps with detailed comments
3. **Architecture**: System design, technology stack, services/interfaces
4. **Refinement**: TDD cycles (Red-Green-Refactor), optimization
5. **Completion**: Integration testing, documentation, deployment

## Multi-Agent Implementation (Agentic Engineering)

- **Sequential**: Changes in defined order
- **Parallel**: Simultaneous processing for large projects  
- **Swarm**: Multiple agents on different aspects
- **Concurrent Async**: Preventing I/O blocking

## Official Tools & Frameworks

### 1. ruvnet/sparc (Primary)
- SPARC CLI (v0.87.7)
- Multi-LLM support (Anthropic, OpenAI, OpenRouter)
- Memory & expert knowledge integration

### 2. agenticsorg/sparc2 (Most Advanced) ⭐
- Diff tracking system (unified diffs)
- Vector store database (semantic code patterns)
- Sandboxed execution (E2B: Python, JS, TS, Go, Rust)
- MCP integration
- 4 modes: Sequential, Parallel, Concurrent, Swarm

### 3. Claude-SPARC Automated System
- Full SPARC + Claude Code CLI
- Parallel batch operations
- TDD (London School)
- Multi-agent memory bank coordination

## Best Practices

- Clear specifications (stakeholder-approved)
- >80% test coverage (unit + integration + E2E)
- Short TDD cycles (<15min)
- Document architectural decisions
- Modular code (≤500 lines/file, ≤50 lines/function)
- Specialized models per phase:
  - o1/o3: Architecture decisions
  - GPT-4o/Claude Sonnet: Implementation
  - Perplexity: Research

## Installation

```bash
npx create-sparc [project-name]
sparc [project] --mode [backend-only|frontend-only|api-only]
```

## Sources
- https://github.com/ruvnet/sparc
- https://github.com/agenticsorg/sparc2
- https://gist.github.com/ruvnet/27ee9b1dc01eec69bc270e2861aa2c05
- https://github.com/ruvnet/claude-flow/wiki/SPARC-Methodology
