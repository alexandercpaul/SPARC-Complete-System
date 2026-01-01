#!/usr/bin/env python3
"""Complete Codex direct API - replicates CLI behavior"""
import requests
import json
import time
from pathlib import Path

class CodexDirectAPI:
    def __init__(self):
        # Load auth
        auth = json.loads((Path.home() / ".codex" / "auth.json").read_text())
        self.access_token = auth["tokens"]["access_token"]
        self.account_id = auth["tokens"]["account_id"]

        self.base_url = "https://chatgpt.com/backend-api/codex"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "chatgpt-account-id": self.account_id,
            "User-Agent": "codex-cli/0.0.0"
        }

    def list_environments(self):
        """List available cloud environments"""
        response = requests.get(
            f"{self.base_url}/environments",
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def create_task(self, prompt, environment_id, branch="main", qa_mode=False, best_of_n=1):
        """Create a new Codex task (replicates CLI)"""

        payload = {
            "new_task": {
                "environment_id": environment_id,
                "branch": branch,
                "run_environment_in_qa_mode": qa_mode
            },
            "input_items": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "content_type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "metadata": {
                "best_of_n": best_of_n
            }
        }

        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json()

    def get_task_details(self, task_id, retries=5):
        """Get task details and output with rate limit handling"""
        for attempt in range(retries):
            try:
                response = requests.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                    print(f"\n⏸️  Rate limited, waiting {wait_time}s...", end="\r")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"\n⏸️  Rate limited, waiting {wait_time}s...", end="\r")
                    time.sleep(wait_time)
                    continue
                raise

        raise Exception("Max retries exceeded for task details")

    def wait_for_completion(self, task_id, timeout=300, poll_interval=5):
        """Poll task until completion with adaptive polling"""
        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            details = self.get_task_details(task_id)
            turn = details.get("current_assistant_turn", {})
            status = turn.get("turn_status")

            print(f"Status: {status}", end="\r")

            if status == "completed":
                return details
            elif status == "error":
                error = turn.get("error", {})
                raise Exception(f"Task failed: {error}")

            # Adaptive polling: start faster, slow down if taking long
            if attempt < 10:
                time.sleep(poll_interval)
            else:
                time.sleep(poll_interval * 2)  # Slower polling after 10 attempts

            attempt += 1

        raise TimeoutError(f"Task did not complete within {timeout}s")

    def extract_response_text(self, task_details):
        """Extract assistant response from task details"""
        turn = task_details.get("current_assistant_turn", {})
        output_items = turn.get("output_items", [])

        # Find message output
        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for part in content:
                    if part.get("content_type") == "text":
                        return part.get("text", "")

        return None

    def call_codex(self, prompt, environment_id=None, wait=True):
        """
        Complete Codex call - create task and wait for response
        (Replicates `codex exec` behavior)
        """

        # Get default environment if not specified
        if not environment_id:
            envs = self.list_environments()
            if not envs:
                raise Exception("No environments available. Create one at chatgpt.com/codex")
            environment_id = envs[0]["id"]
            print(f"Using environment: {envs[0]['label']}")

        # Create task
        print(f"Creating task...")
        result = self.create_task(prompt, environment_id)
        task_id = result["task"]["id"]
        print(f"Task ID: {task_id}")

        if not wait:
            return {"task_id": task_id, "status": "pending"}

        # Wait for completion
        print(f"Waiting for response...")
        details = self.wait_for_completion(task_id)

        # Extract response
        response_text = self.extract_response_text(details)

        print()  # Clear status line
        return {
            "task_id": task_id,
            "status": "completed",
            "response": response_text,
            "full_details": details
        }


if __name__ == "__main__":
    # Test the API
    codex = CodexDirectAPI()

    print("=" * 80)
    print("🚀 Codex Direct API Test")
    print("=" * 80)
    print()

    # Simple test
    result = codex.call_codex("Write a Python function to calculate factorial. Keep it under 5 lines.")

    print("=" * 80)
    print("✅ Response:")
    print("=" * 80)
    print(result["response"])
    print("=" * 80)
    print()
    print(f"Task ID: {result['task_id']}")
    print()
    print("🎉 Codex direct API fully operational!")
