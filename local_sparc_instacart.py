#!/usr/bin/env python3
"""
Local Ollama SPARC - Voice Command Parser for Instacart
Runs in parallel with cloud SPARC (FREE and FAST!)
"""
import requests, json, time

class LocalSPARC:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        print("=" * 80)
        print("🏠 LOCAL Ollama SPARC - Instacart Voice Parser")
        print("=" * 80)
        print("Building: Voice → Grocery List converter")
        print("Model: sparc-qwen (7.6B, SPARC-trained)")
        print("Cost: $0 (local, unlimited)")
        print("=" * 80)
        print()

    def ollama_call(self, prompt, model="sparc-qwen"):
        start = time.time()
        response = requests.post(
            self.ollama_url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        latency = (time.time() - start) * 1000
        result = response.json()["response"]
        print(f"    ⚡ {latency:.0f}ms | {len(result)} chars")
        return result

    def run(self):
        start_time = time.time()

        # Phase 1: Spec
        print("📋 Phase 1: Specification")
        print("-" * 80)
        spec = self.ollama_call("""Using SPARC methodology, create a specification for a voice command parser that converts spoken grocery requests into structured Instacart orders.

Requirements:
- Parse natural language: "I need milk, bread, and eggs"
- Extract items, quantities, preferences
- Handle variations: "get me", "I want", "add to cart"
- Output structured JSON for Instacart API

Keep it concise (500 words).""")
        print(f"  ✅ Spec: {len(spec)} chars\n")

        # Phase 2: Pseudocode
        print("🧮 Phase 2: Pseudocode")
        print("-" * 80)
        pseudocode = self.ollama_call(f"""Based on this spec, write pseudocode for the voice command parser:

{spec[:2000]}

Include:
1. Voice input processing
2. NLP parsing algorithm
3. Item extraction
4. Quantity detection
5. JSON output formation

Use clear step-by-step logic.""")
        print(f"  ✅ Pseudocode: {len(pseudocode)} chars\n")

        # Phase 3: Architecture
        print("🏗️  Phase 3: Architecture")
        print("-" * 80)
        architecture = self.ollama_call(f"""Design system architecture for:

{pseudocode[:1500]}

Include:
1. Component breakdown
2. Data flow
3. API structure
4. Error handling

Be specific.""")
        print(f"  ✅ Architecture: {len(architecture)} chars\n")

        # Phase 4: Implementation
        print("💻 Phase 4: Implementation")
        print("-" * 80)
        code = self.ollama_call(f"""Implement this voice parser in Python:

{architecture[:1500]}

Write production-ready code with:
1. Voice input handling
2. NLP parsing (use spaCy or simple regex)
3. Item extraction
4. JSON output
5. Type hints and docstrings

Complete working code.""", model="qwen2.5-coder:7b")
        print(f"  ✅ Code: {len(code)} chars\n")

        # Phase 5: Tests
        print("🧪 Phase 5: Tests")
        print("-" * 80)
        tests = self.ollama_call(f"""Generate pytest tests for:

{code[:2000]}

Test cases:
1. "I need milk" → {{"items": [{{"name": "milk"}}]}}
2. "Get me 2 dozen eggs" → quantity parsing
3. "Add bread and butter" → multiple items
4. Edge cases

Use pytest.""", model="qwen2.5-coder:7b")
        print(f"  ✅ Tests: {len(tests)} chars\n")

        total_time = time.time() - start_time

        # Save
        result = {
            "specification": spec,
            "pseudocode": pseudocode,
            "architecture": architecture,
            "code": code,
            "tests": tests
        }

        import json
        from pathlib import Path
        output_path = Path("/tmp/local_sparc_voice_parser.json")
        output_path.write_text(json.dumps(result, indent=2))

        print("=" * 80)
        print("🎉 LOCAL SPARC Complete!")
        print("=" * 80)
        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"💰 Cost: $0 (local Ollama)")
        print(f"📁 Saved: {output_path}")
        print("=" * 80)

        return result

if __name__ == "__main__":
    sparc = LocalSPARC()
    result = sparc.run()
    print("\n✅ Voice parser ready!")
