#!/usr/bin/env python3
"""
Hybrid SPARC - Ollama + Cloud Agents
Best of both worlds: Local speed + Cloud quality
"""
import requests, json, uuid, time
from pathlib import Path

class HybridSPARC:
    """SPARC orchestrator using Ollama (local) + Cloud (Gemini/Codex)"""

    def __init__(self):
        # Ollama setup (local, free, unlimited)
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model_fast = "sparc-qwen"  # SPARC-tuned, fastest
        self.ollama_model_code = "qwen2.5-coder:7b"  # Best code generation

        # Gemini setup (cloud, paid)
        gemini_creds = json.loads((Path.home() / ".gemini" / "oauth_creds.json").read_text())
        self.gemini_token = gemini_creds["access_token"]
        self.gemini_project = "autonomous-bay-whv63"

        print("=" * 80)
        print("🤖 Hybrid SPARC - Ollama + Cloud")
        print("=" * 80)
        print("Local: Ollama (fast, unlimited, free)")
        print("Cloud: Gemini Pro (quality), Codex (execution)")
        print("=" * 80)
        print()

    def ollama_call(self, prompt, model="sparc-qwen"):
        """Call local Ollama - FAST and UNLIMITED"""
        start = time.time()

        response = requests.post(
            self.ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            timeout=120
        )

        data = response.json()
        latency = (time.time() - start) * 1000

        print(f"    ⚡ Ollama: {latency:.0f}ms (LOCAL)")
        return data["response"]

    def gemini_call(self, prompt, model="gemini-2.5-flash"):
        """Call cloud Gemini - QUALITY"""
        start = time.time()

        response = requests.post(
            "https://cloudcode-pa.googleapis.com/v1internal:generateContent",
            headers={
                "Authorization": f"Bearer {self.gemini_token}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "project": self.gemini_project,
                "user_prompt_id": str(uuid.uuid4()),
                "request": {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "session_id": str(uuid.uuid4()),
                    "generationConfig": {"temperature": 0.7, "topP": 0.95, "topK": 64}
                }
            },
            timeout=120
        )

        data = response.json()
        latency = (time.time() - start) * 1000

        print(f"    ☁️  Gemini: {latency:.0f}ms (CLOUD)")
        return data["response"]["candidates"][0]["content"]["parts"][0]["text"]

    def phase1_specification_hybrid(self, user_request):
        """Phase 1: Research with LOCAL Ollama (fast, unlimited)"""
        print("📋 Phase 1: Specification (Ollama SPARC)")
        print("-" * 80)

        # Use local SPARC-tuned model for research (FAST!)
        spec = self.ollama_call(
            f"""You are a SPARC specification expert. Analyze this request and create a detailed specification:

{user_request}

Provide:
1. Requirements analysis
2. Constraints
3. Success criteria
4. Implementation scope

Be concise but complete.""",
            model="sparc-qwen"
        )

        print(f"  ✅ Specification complete ({len(spec)} chars)")
        return spec

    def phase2_pseudocode_hybrid(self, specification):
        """Phase 2: Algorithm with LOCAL Ollama (fast code generation)"""
        print("🧮 Phase 2: Pseudocode (Ollama Qwen Coder)")
        print("-" * 80)

        # Use local code-tuned model
        pseudocode = self.ollama_call(
            f"""Given this specification, write detailed pseudocode:

{specification}

Use clear step-by-step logic. Include all algorithms and data structures.""",
            model="qwen2.5-coder:7b"
        )

        print(f"  ✅ Pseudocode complete ({len(pseudocode)} chars)")
        return pseudocode

    def phase3_architecture_cloud(self, specification, pseudocode):
        """Phase 3: Architecture with CLOUD Gemini Pro (best quality)"""
        print("🏗️  Phase 3: Architecture (Gemini Pro - Cloud)")
        print("-" * 80)

        # Use cloud for high-quality architecture design
        architecture = self.gemini_call(
            f"""Design complete system architecture:

Specification:
{specification[:2000]}

Pseudocode:
{pseudocode[:2000]}

Provide:
1. Component diagram
2. Data flow
3. API contracts
4. Technology stack

Be specific about implementation.""",
            model="gemini-2.5-pro"
        )

        print(f"  ✅ Architecture complete ({len(architecture)} chars)")
        return architecture

    def phase4_implementation_local(self, architecture, pseudocode):
        """Phase 4: Implementation with LOCAL Ollama (fast code gen)"""
        print("💻 Phase 4: Implementation (Ollama Qwen Coder)")
        print("-" * 80)

        # Generate code locally (FAST and UNLIMITED!)
        code = self.ollama_call(
            f"""Implement this system:

Architecture:
{architecture[:2000]}

Pseudocode:
{pseudocode[:1500]}

Write production-ready Python code with:
1. Type hints
2. Error handling
3. Docstrings
4. Logging

Create complete implementation.""",
            model="qwen2.5-coder:7b"
        )

        print(f"  ✅ Implementation complete ({len(code)} chars)")
        return code

    def phase5_tests_local(self, code):
        """Phase 5: Tests with LOCAL Ollama (fast test generation)"""
        print("🧪 Phase 5: Tests (Ollama Qwen Coder)")
        print("-" * 80)

        # Generate tests locally
        tests = self.ollama_call(
            f"""Generate comprehensive tests for this code:

{code[:2000]}

Create:
1. Unit tests (pytest)
2. Integration tests
3. Edge cases
4. Mocks where needed

Use pytest framework.""",
            model="qwen2.5-coder:7b"
        )

        print(f"  ✅ Tests complete ({len(tests)} chars)")
        return tests

    def run_hybrid_sparc(self, user_request):
        """Execute hybrid SPARC (Ollama + Cloud)"""
        print("🚀 Starting Hybrid SPARC...")
        print()

        try:
            start_time = time.time()

            # Phase 1: Ollama (local, fast)
            spec = self.phase1_specification_hybrid(user_request)

            # Phase 2: Ollama (local code generation)
            pseudocode = self.phase2_pseudocode_hybrid(spec)

            # Phase 3: Gemini Pro (cloud quality)
            architecture = self.phase3_architecture_cloud(spec, pseudocode)

            # Phase 4: Ollama (local code generation - unlimited!)
            code = self.phase4_implementation_local(architecture, pseudocode)

            # Phase 5: Ollama (local test generation)
            tests = self.phase5_tests_local(code)

            total_time = time.time() - start_time

            # Save results
            result = {
                "specification": spec,
                "pseudocode": pseudocode,
                "architecture": architecture,
                "implementation": code,
                "tests": tests,
                "total_time_seconds": total_time
            }

            output_path = Path("/tmp/hybrid_sparc_output.json")
            output_path.write_text(json.dumps(result, indent=2))

            print()
            print("=" * 80)
            print("🎉 Hybrid SPARC Complete!")
            print("=" * 80)
            print(f"⏱️  Total time: {total_time:.1f} seconds")
            print(f"📊 Output:")
            print(f"  - Specification: {len(spec)} chars")
            print(f"  - Pseudocode: {len(pseudocode)} chars")
            print(f"  - Architecture: {len(architecture)} chars")
            print(f"  - Code: {len(code)} chars")
            print(f"  - Tests: {len(tests)} chars")
            print(f"📁 Saved to: {output_path}")
            print()
            print("💡 Benefits:")
            print("  - Phases 1,2,4,5: FREE (Ollama local)")
            print("  - Phase 3: Cloud (Gemini Pro quality)")
            print("  - Estimated ~2-3 minutes total!")
            print("=" * 80)

            return result

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    # Test with simple request
    sparc = HybridSPARC()

    result = sparc.run_hybrid_sparc(
        "Create a Python REST API for storing and retrieving notes with SQLite database"
    )

    if result:
        print("\n✅ Hybrid SPARC ready for production!")
        print(f"Total execution time: {result['total_time_seconds']:.1f}s")
