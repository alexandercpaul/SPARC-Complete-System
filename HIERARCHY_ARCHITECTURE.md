# 3-Tier Agent Hierarchy: Architecture

This document outlines the architecture of the 3-tier agent hierarchy, consisting of Claude (CEO), Gemini (Middle Manager), and Ollama Workers.

## 1. Tier 1: Claude (CEO)

-   **Role**: The "CEO" of the hierarchy, responsible for defining high-level goals and delegating tasks.
-   **Interaction**: Claude (in this case, the user) initiates a task by running the Gemini Manager script with a natural language prompt.
    ```bash
    /tmp/gemini_manager.sh "Analyze the code in /path/to/file.js and suggest improvements."
    ```

## 2. Tier 2: Gemini (Middle Manager)

-   **Role**: The "Middle Manager" that receives tasks from Claude, coordinates the workforce, and reports back.
-   **Script**: `/tmp/gemini_manager.sh`
-   **Coordination Workflow**:
    1.  **Task Intake**: The script receives the task description as a command-line argument.
    2.  **Trace ID Generation**: A unique `trace_id` is created to track the task's lifecycle across all systems.
    3.  **Worker Selection (Routing)**: The manager uses simple keyword matching on the task description to select the most appropriate Ollama worker.
        -   "image", "vision", "screenshot" -> `ollama_vision_worker.sh`
        -   "code", "analyze", "script" -> `ollama_code_worker.sh`
        -   (Default) -> `ollama_research_worker.sh`
    4.  **Delegation**: The manager executes the selected worker script in the background, passing the `trace_id` and the original prompt.
    5.  **Monitoring & Inspection**: The manager immediately starts monitoring the `/tmp/ollama_workers/artifacts` directory. This is the **interweave inspection pattern**. It doesn't wait for the worker to finish blindly; it waits for the artifact file to be created, which signals that the worker has begun producing output. This pattern allows for future extensions where the manager could inspect the artifact mid-process.
    6.  **Reporting**: Once the worker process completes, the manager script reads the final artifact, extracts the last few lines as "key findings," and formats a report for Claude, which is printed to standard output.

## 3. Tier 3: Ollama Workers

-   **Role**: Specialized "Workers" that perform the actual task execution using specific LLMs.
-   **Scripts**:
    -   `/tmp/ollama_vision_worker.sh` (llava)
    -   `/tmp/ollama_research_worker.sh` (llama3.2)
    -   `/tmp/ollama_code_worker.sh` (qwen2.5-coder)
-   **Core Responsibilities**:
    1.  **Structured Logging**: On start, each worker creates a structured JSON log in `/tmp/ollama_workers/logs`, containing metadata about the job. This log is updated upon completion.
    2.  **Tracing**: All log entries are also appended to a shared trace file (`/tmp/ollama_workers/traces/<trace_id>.trace.jsonl`), providing a consolidated view of the entire task flow.
    3.  **Artifact Generation**: The primary output of the worker's LLM call is saved to a file in `/tmp/ollama_workers/artifacts`. This is the inspectable result of their work.

## 4. Token Savings Analysis

This hierarchical model provides significant token savings compared to using a single, powerful model (like Claude 3 Opus or Gemini 1.5 Pro) for all tasks.

-   **Claude/Gemini Pro (High-Cost Models)**: These models are used for high-level reasoning, planning, and synthesis. In this architecture, their use is limited to:
    -   The initial user prompt (by Claude).
    -   The Gemini manager's internal logic (which is scripted, so **zero token cost** for orchestration).
    -   The final review of the report by Claude.
-   **Ollama (Low-Cost/Free Models)**: The bulk of the work—code analysis, research, image description—is offloaded to locally-run Ollama models. These models are smaller, specialized, and have **zero direct API cost**.

**Example Cost Breakdown:**

Assume a complex code analysis task:

-   **Monolithic Approach (Claude-only)**:
    -   Input Prompt: 1,000 tokens
    -   Code to Analyze: 10,000 tokens
    -   Output/Analysis: 2,000 tokens
    -   **Total Cost**: ~13,000 tokens processed by a high-cost model.

-   **Hierarchical Approach (This Project)**:
    -   **Claude -> Gemini**:
        -   Input Prompt: 1,000 tokens (delegated)
        -   **Cost**: User provides prompt, no model cost.
    -   **Gemini -> Ollama**:
        -   Orchestration: 0 tokens (scripted logic).
    -   **Ollama Worker**:
        -   Code + Prompt: 11,000 tokens processed by `qwen2.5-coder` (free).
        -   Output written to artifact.
    -   **Gemini -> Claude (Report)**:
        -   Report Generation: 0 tokens (scripted).
        -   Report contains a *summary* of the artifact, not the full text.
    -   **Total Cost**: The only "cost" is the electricity to run the local Ollama model. The expensive foundational model is only used for the initial prompt and final review, not the heavy lifting.

This demonstrates a massive reduction in token consumption for the most expensive models, making the system highly efficient and scalable.
