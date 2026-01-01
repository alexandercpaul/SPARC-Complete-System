#!/usr/bin/env python3
"""
SPARC Memory Extension Project
Solve Claude Code's 200K context limitation using MCP memory server
"""
import requests, json, uuid, sys, time
from pathlib import Path
from codex_direct_api_complete import CodexDirectAPI

class SPARCMemoryProject:
    def __init__(self):
        # Gemini setup
        gemini_creds = json.loads((Path.home() / ".gemini" / "oauth_creds.json").read_text())
        self.gemini_token = gemini_creds["access_token"]
        self.gemini_project = "autonomous-bay-whv63"

        # Codex setup
        self.codex = CodexDirectAPI()

        print("=" * 80)
        print("🧠 SPARC Memory Extension Project")
        print("=" * 80)
        print("Goal: Solve Claude Code's 200K context limitation")
        print("Method: Build MCP memory server with vector storage")
        print("Agents: Unlimited Gemini + Codex sub-agents")
        print("=" * 80)
        print()

    def gemini_call(self, prompt, model="gemini-2.5-flash", retries=3):
        """Direct Gemini API call with rate limit handling"""
        call_start = time.time()

        for attempt in range(retries):
            api_start = time.time()
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

            # Handle rate limits
            if response.status_code == 429:
                wait_time = 5 * (attempt + 1)  # Exponential backoff
                print(f"    ⏸️  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            # Handle other errors
            if "error" in data:
                if attempt < retries - 1:
                    print(f"    ⚠️  Error (attempt {attempt + 1}/{retries}): {data['error'].get('message', 'Unknown')}")
                    time.sleep(3)
                    continue
                else:
                    raise Exception(f"Gemini API error: {data['error']}")

            # Success
            api_latency = (time.time() - api_start) * 1000  # ms
            total_latency = (time.time() - call_start) * 1000  # ms
            print(f"    ⏱️  API: {api_latency:.0f}ms | Total: {total_latency:.0f}ms")
            return data["response"]["candidates"][0]["content"]["parts"][0]["text"]

        raise Exception("Max retries exceeded")

    def codex_call(self, prompt):
        """Direct Codex API call"""
        result = self.codex.call_codex(prompt)
        return result["response"]

    def phase1_specification(self):
        """Phase 1: Research & Specification (Gemini Flash)"""
        phase_start = time.time()
        print("📋 Phase 1: Specification & Research")
        print("-" * 80)

        # Spawn multiple Gemini agents for parallel research
        research_topics = [
            "MCP (Model Context Protocol) server specification and best practices",
            "Vector databases suitable for conversation memory (ChromaDB, Pinecone, Weaviate)",
            "Claude Code MCP integration patterns and configuration",
            "Memory retrieval strategies (RAG, semantic search, hybrid approaches)"
        ]

        research_results = []
        for i, topic in enumerate(research_topics, 1):
            print(f"  🔍 Agent {i}/{len(research_topics)}: Researching {topic[:50]}...")

            # Rate limit protection - wait between calls
            if i > 1:
                time.sleep(5)

            result = self.gemini_call(
                f"""Research this topic thoroughly:

{topic}

Provide:
1. Key concepts and definitions
2. Best practices
3. Recommended approaches
4. Potential challenges
5. Implementation considerations

Be concise but comprehensive.""",
                model="gemini-2.5-flash"  # Use Flash for research (higher rate limits)
            )
            research_results.append({
                "topic": topic,
                "findings": result
            })
            print(f"    ✅ Complete ({len(result)} chars)")

        # Synthesize into specification
        print(f"\n  🧠 Synthesizing specification...")
        synthesis_prompt = f"""Based on these research findings, create a comprehensive specification for a Claude Code memory extension system:

{chr(10).join([f"### {r['topic']}\n{r['findings']}\n" for r in research_results])}

Create a specification that includes:
1. **System Overview**: What we're building and why
2. **Requirements**: Functional and non-functional requirements
3. **Architecture Constraints**: Technology choices and limitations
4. **Success Criteria**: How we measure success
5. **Implementation Scope**: What's in/out of scope for v1

Be detailed and actionable."""

        specification = self.gemini_call(synthesis_prompt, model="gemini-2.5-pro")

        print(f"  ✅ Specification complete ({len(specification)} chars)")
        print()

        return {
            "research": research_results,
            "specification": specification
        }

    def phase2_pseudocode(self, specification):
        """Phase 2: Algorithm Design (Gemini Flash)"""
        print("🧮 Phase 2: Pseudocode & Algorithm Design")
        print("-" * 80)

        prompt = f"""Given this specification for a Claude Code memory extension:

{specification}

Design the core algorithms in detailed pseudocode:

1. **Memory Storage Algorithm**: How to store conversations with embeddings
2. **Memory Retrieval Algorithm**: How to search and retrieve relevant context
3. **Context Window Management**: How to prioritize what fits in 200K
4. **MCP Server Protocol**: Request/response handling
5. **Integration Flow**: How Claude Code uses the memory system

Use clear, step-by-step pseudocode with proper structure."""

        print("  💭 Designing algorithms...")
        pseudocode = self.gemini_call(prompt, model="gemini-2.5-flash")

        print(f"  ✅ Pseudocode complete ({len(pseudocode)} chars)")
        print()

        return pseudocode

    def phase3_architecture(self, specification, pseudocode):
        """Phase 3: System Architecture (Gemini Pro)"""
        print("🏗️  Phase 3: System Architecture")
        print("-" * 80)

        prompt = f"""Design the complete system architecture for this memory extension:

Specification:
{specification}

Algorithms:
{pseudocode}

Provide:
1. **Component Diagram**: All major components and their responsibilities
2. **Data Flow**: How data moves through the system
3. **API Contracts**: MCP protocol endpoints and schemas
4. **Data Models**: Database schemas and object models
5. **Technology Stack**: Specific libraries and tools to use
6. **File Structure**: Project organization
7. **Integration Points**: How Claude Code connects

Be specific about implementation details."""

        print("  🎨 Designing architecture...")
        architecture = self.gemini_call(prompt, model="gemini-2.5-pro")

        print(f"  ✅ Architecture complete ({len(architecture)} chars)")
        print()

        return architecture

    def phase4_implementation(self, architecture, pseudocode):
        """Phase 4: Code Implementation (Codex Cloud)"""
        print("💻 Phase 4: Implementation")
        print("-" * 80)

        # Spawn multiple Codex agents for parallel implementation
        components = [
            {
                "name": "MCP Server Core",
                "description": "Main MCP server with protocol handling"
            },
            {
                "name": "Vector Storage Layer",
                "description": "Vector database integration for embeddings"
            },
            {
                "name": "Memory Manager",
                "description": "Store and retrieve conversation memories"
            },
            {
                "name": "Context Optimizer",
                "description": "Select most relevant memories for 200K window"
            }
        ]

        implementations = []
        for i, component in enumerate(components, 1):
            print(f"  🤖 Codex Agent {i}/{len(components)}: Implementing {component['name']}...")

            prompt = f"""Implement this component based on the architecture:

Component: {component['name']}
Description: {component['description']}

Architecture:
{architecture[:2000]}  # Truncate to avoid token limits

Pseudocode:
{pseudocode[:2000]}

Write production-ready Python code with:
1. Proper error handling
2. Type hints
3. Docstrings
4. Logging
5. Configuration management

Create a complete, working implementation."""

            code = self.codex_call(prompt)
            implementations.append({
                "component": component['name'],
                "code": code
            })
            print(f"    ✅ Complete")

        # Integrate components
        print(f"\n  🔗 Integrating components...")
        integration_prompt = f"""Integrate these components into a cohesive system:

{chr(10).join([f"### {impl['component']}\n{impl['code']}\n" for impl in implementations])}

Create:
1. Main entry point (server.py)
2. Configuration file (config.yaml)
3. Installation script (install.sh)
4. README with setup instructions

Ensure all components work together."""

        integration = self.codex_call(integration_prompt)

        print(f"  ✅ Integration complete")
        print()

        return {
            "components": implementations,
            "integration": integration
        }

    def phase5_completion(self, implementation):
        """Phase 5: Testing & Documentation (Gemini Pro)"""
        print("🧪 Phase 5: Testing & Documentation")
        print("-" * 80)

        # Generate tests
        print("  🧪 Generating test suite...")
        test_prompt = f"""Generate comprehensive tests for this memory extension system:

{implementation['integration'][:3000]}

Create:
1. **Unit Tests**: Test each component in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test full Claude Code integration
4. **Performance Tests**: Measure retrieval latency
5. **Test Data**: Sample conversations and queries

Use pytest framework."""

        tests = self.gemini_call(test_prompt, model="gemini-2.5-pro")

        print(f"    ✅ Tests complete ({len(tests)} chars)")

        # Generate documentation
        print("  📚 Generating documentation...")
        doc_prompt = f"""Create comprehensive documentation:

System:
{implementation['integration'][:3000]}

Include:
1. **User Guide**: How to install and use
2. **Architecture Overview**: System design
3. **API Reference**: MCP endpoints
4. **Configuration**: All options explained
5. **Troubleshooting**: Common issues
6. **Performance Tuning**: Optimization tips

Make it beginner-friendly but thorough."""

        documentation = self.gemini_call(doc_prompt, model="gemini-2.5-pro")

        print(f"    ✅ Documentation complete ({len(documentation)} chars)")
        print()

        return {
            "tests": tests,
            "documentation": documentation
        }

    def run_sparc(self):
        """Execute complete SPARC workflow"""
        print("🚀 Starting SPARC Workflow...")
        print()

        try:
            # Phase 1: Specification
            phase1_result = self.phase1_specification()

            # Phase 2: Pseudocode
            phase2_result = self.phase2_pseudocode(phase1_result["specification"])

            # Phase 3: Architecture
            phase3_result = self.phase3_architecture(
                phase1_result["specification"],
                phase2_result
            )

            # Phase 4: Implementation
            phase4_result = self.phase4_implementation(
                phase3_result,
                phase2_result
            )

            # Phase 5: Completion
            phase5_result = self.phase5_completion(phase4_result)

            # Package results
            complete_system = {
                "specification": phase1_result["specification"],
                "research": phase1_result["research"],
                "pseudocode": phase2_result,
                "architecture": phase3_result,
                "implementation": phase4_result,
                "tests": phase5_result["tests"],
                "documentation": phase5_result["documentation"]
            }

            # Save everything
            output_path = Path("/tmp/memory_extension_system.json")
            output_path.write_text(json.dumps(complete_system, indent=2))

            print("=" * 80)
            print("🎉 SPARC COMPLETE!")
            print("=" * 80)
            print(f"📦 Complete system saved to: {output_path}")
            print()
            print("📊 Summary:")
            print(f"  - Research agents spawned: 4")
            print(f"  - Code agents spawned: 5")
            print(f"  - Total phases: 5")
            print(f"  - Components built: {len(phase4_result['components'])}")
            print()
            print("🎯 Next Steps:")
            print("  1. Review the generated code")
            print("  2. Run the tests")
            print("  3. Deploy the MCP server")
            print("  4. Configure Claude Code to use it")
            print("=" * 80)

            return complete_system

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    sparc = SPARCMemoryProject()
    result = sparc.run_sparc()

    if result:
        print("\n✅ Memory extension system ready for deployment!")
    else:
        print("\n❌ SPARC workflow encountered errors")
        sys.exit(1)
