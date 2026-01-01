
# Bidirectional Communication Protocol: Claude <> Gemini Brain

This document outlines the communication protocol between Claude (the primary LLM) and Gemini (the external brain). The protocol is inspired by the Model Context Protocol (MCP) and the LLM Agent Communication Protocol (LACP).

## 1. Overview

The protocol is designed to be:

- **Bidirectional:** Both Claude and Gemini can initiate communication.
- **Asynchronous:** Neither party is blocked while waiting for a response.
- **Structured:** Messages are in JSON-RPC 2.0 format.
- **Extensible:** New methods and notifications can be added easily.

## 2. Transport

Communication will occur over a local WebSocket connection. Gemini will expose a WebSocket server, and Claude will connect as a client.

## 3. Message Format

All messages are JSON-RPC 2.0 objects with the following properties:

- `jsonrpc`: "2.0"
- `method`: The name of the method or notification.
- `params`: An object containing the parameters.
- `id`: A unique identifier for requests (absent for notifications).

## 4. Claude -> Gemini Communication

### 4.1. Requests

- **`memory.store`**: Store information in Geminis persistent memory.
  - `params`: `{ "key": "...", "value": "..." }`
- **`memory.retrieve`**: Retrieve information from Geminis persistent memory.
  - `params`: `{ "key": "..." }`
- **`research.search`**: Perform a web search.
  - `params`: `{ "query": "..." }`
- **`data.process`**: Process a large amount of data (e.g., summarize a file).
  - `params`: `{ "data": "..." }`

### 4.2. Notifications

- **`state.update`**: Inform Gemini of Claudes current state.
  - `params`: `{ "token_usage": { "current": ..., "total": ... } }`

## 5. Gemini -> Claude Communication

### 5.1. Requests

- **`context.inject`**: Inject information into Claudes context.
  - `params`: `{ "data": "..." }`
- **`action.suggest`**: Suggest an action for Claude to take.
  - `params`: `{ "action": "..." }`

### 5.2. Notifications

- **`alert.hallucination_risk`**: Warn Claude of a high risk of hallucination.
  - `params`: `{ "token_percentage": ... }`
- **`alert.memory_full`**: Inform Claude that its context window is nearing capacity.
  - `params`: `{ "token_percentage": ... }`

## 6. When to Interject

Gemini should interject and communicate with Claude when:

- **Hallucination Risk:** Claudes token usage exceeds 95%.
- **Memory Full:** Claudes token usage exceeds 90%.
- **Relevant Information Retrieved:** Gemini finds information in its persistent memory that is relevant to the current conversation.
- **External Event:** An external event occurs that requires Claudes attention (e.g., a new email arrives).

## 7. Saving and Restoring Context

- **Saving:** Claude will periodically send `state.update` notifications to Gemini. Gemini will store the context (including conversation history and other relevant data) in its persistent memory.
- **Restoring:** When a new session starts, Gemini will use the `context.inject` request to restore the previous context into Claudes context window.

