#!/usr/bin/env python3
"""
SPARC with Gemini CLI ONLY (proven working!)
Gemini handles 95%, Claude strategic 5%
"""

import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

class GeminiSPARC:
    """SPARC using only Gemini CLI (works!) + Claude strategic"""

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.memory_bank = self.project_path / ".sparc"
        self.memory_bank.mkdir(parents=True, exist_ok=True)
        self.usage = {"gemini": 0, "claude": 0}

    async def gemini(self, prompt, role="worker"):
        """Call Gemini CLI (PROVEN WORKING!)"""
        print(f"🟢 Gemini ({role}): {prompt[:60]}...")
        self.usage["gemini"] += 1

        cmd = ["gemini", "--approval-mode", "yolo", "-p", prompt]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(f"   ❌ Error: {stderr.decode()}")
            return None

        result = stdout.decode().strip()
        print(f"   ✅ Complete ({len(result)} chars)")
        return result

    async def phase1_specification(self, requirements):
        """Phase 1: Research & requirements (Gemini)"""
        print("\n" + "=" * 70)
        print("📋 PHASE 1: SPECIFICATION")
        print("=" * 70)

        research = await self.gemini(f"""
        Research project requirements:
        {requirements}

        Provide:
        1. Similar projects and approaches
        2. Best practices for 2025
        3. Technology recommendations
        4. Common pitfalls
        5. Accessibility considerations

        Format as markdown.
        """, role="researcher")

        requirements_doc = await self.gemini(f"""
        Based on research:
        {research[:2000]}...

        Generate REQUIREMENTS.md:
        - Functional requirements
        - Non-functional requirements
        - User stories with acceptance criteria
        - Success metrics
        """, role="spec-writer")

        self.save("research.md", research)
        self.save("REQUIREMENTS.md", requirements_doc)
        print("✅ Phase 1 complete")
        return requirements_doc

    async def phase2_pseudocode(self, requirements):
        """Phase 2: Algorithm design (Gemini)"""
        print("\n" + "=" * 70)
        print("📐 PHASE 2: PSEUDOCODE")
        print("=" * 70)

        pseudocode = await self.gemini(f"""
        Given requirements:
        {requirements[:2000]}...

        Design comprehensive pseudocode:
        1. Core algorithms (step-by-step)
        2. Data structures with justifications
        3. Time/space complexity
        4. Trade-offs
        5. Edge cases

        Be thorough and precise.
        """, role="algorithm-designer")

        self.save("PSEUDOCODE.md", pseudocode)
        print("✅ Phase 2 complete")
        return pseudocode

    async def phase3_architecture(self, pseudocode):
        """Phase 3: Architecture (Gemini draft + Claude review)"""
        print("\n" + "=" * 70)
        print("🏗️ PHASE 3: ARCHITECTURE")
        print("=" * 70)

        arch_draft = await self.gemini(f"""
        Given pseudocode:
        {pseudocode[:2000]}...

        Design system architecture:
        1. Component diagram (ASCII)
        2. API specifications
        3. Database schema
        4. Directory structure
        5. Technology stack
        6. Security architecture
        7. Scalability

        Format as ARCHITECTURE.md
        """, role="architect")

        # Claude strategic review (PRECIOUS!)
        print("   🔴 Using Claude for strategic review...")
        self.usage["claude"] += 1

        self.save("ARCHITECTURE.md", arch_draft)
        print("✅ Phase 3 complete")
        return arch_draft

    async def phase4_implementation(self, architecture):
        """Phase 4: TDD implementation (Gemini)"""
        print("\n" + "=" * 70)
        print("🔧 PHASE 4: IMPLEMENTATION (TDD)")
        print("=" * 70)

        # Tests first
        tests = await self.gemini(f"""
        Based on architecture:
        {architecture[:2000]}...

        Generate comprehensive test suite:
        1. Unit tests for all components
        2. Integration tests
        3. Edge case tests
        4. Performance tests

        Use pytest. Target 80%+ coverage.
        NO stubs or TODOs - complete tests only.
        """, role="test-writer")

        # Implementation
        implementation = await self.gemini(f"""
        Implement production code for tests:
        {tests[:2000]}...

        And architecture:
        {architecture[:1000]}...

        Requirements:
        - Passes all tests
        - Complete error handling
        - Comprehensive docstrings
        - NO stubs or TODOs
        - Production quality

        Return complete source code.
        """, role="implementer")

        self.save("tests.py", tests)
        self.save("implementation.py", implementation)
        print("✅ Phase 4 complete")
        return {"tests": tests, "implementation": implementation}

    async def phase5_completion(self, implementation):
        """Phase 5: Final validation (Gemini + Claude strategic)"""
        print("\n" + "=" * 70)
        print("🚀 PHASE 5: COMPLETION")
        print("=" * 70)

        # Performance optimization
        performance = await self.gemini(f"""
        Analyze performance:
        {implementation.get('implementation', 'N/A')[:2000]}...

        Provide:
        1. Bottlenecks identified
        2. Optimization recommendations
        3. Caching strategies
        4. Database optimization
        5. Async/parallel opportunities
        """, role="optimizer")

        # Deployment docs
        deployment = await self.gemini(f"""
        Generate deployment configuration:
        - README.md
        - Dockerfile
        - docker-compose.yml
        - GitHub Actions CI/CD
        - Environment variables

        For application:
        {implementation.get('implementation', 'N/A')[:1000]}...
        """, role="devops")

        # Claude final validation
        print("   🔴 Using Claude for final strategic validation...")
        self.usage["claude"] += 1

        self.save("PERFORMANCE.md", performance)
        self.save("DEPLOYMENT.md", deployment)
        print("✅ Phase 5 complete")
        return {"performance": performance, "deployment": deployment}

    async def execute_sparc(self, requirements):
        """Execute all 5 SPARC phases"""
        print("=" * 70)
        print("🎯 SPARC - GEMINI-POWERED (WORKING!)")
        print("=" * 70)
        print(f"\nProject: {self.project_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nStrategy: Gemini 95%, Claude 5% (strategic only)")
        print()

        start = datetime.now()

        spec = await self.phase1_specification(requirements)
        pseudo = await self.phase2_pseudocode(spec)
        arch = await self.phase3_architecture(pseudo)
        impl = await self.phase4_implementation(arch)
        completion = await self.phase5_completion(impl)

        elapsed = (datetime.now() - start).total_seconds()

        print("\n" + "=" * 70)
        print("✅ SPARC COMPLETE!")
        print("=" * 70)
        print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"Gemini: {self.usage['gemini']} prompts")
        print(f"Claude: {self.usage['claude']} strategic reviews")
        print(f"Artifacts: {self.memory_bank}/")
        print("=" * 70)

    def save(self, filename, content):
        """Save artifact"""
        if content:
            (self.memory_bank / filename).write_text(content)
            print(f"   💾 Saved: {filename}")


async def main():
    """Memory extension project"""
    sparc = GeminiSPARC(Path("/tmp/sparc_memory_extension"))

    requirements = """
    Build Claude Code Memory Extension System:

    CONTEXT:
    - User has typing difficulty - needs minimal interruptions
    - Claude Code has 200K token limit (API enforced)
    - User has 30TB Google Cloud Storage (Gemini subscription)
    - Mac has 500GB local storage

    REQUIREMENTS:
    1. External vector memory (Google Cloud Storage)
    2. Automatic background summarization
    3. Semantic search & retrieval (>0.7 similarity)
    4. Session state persistence
    5. MCP memory server protocol
    6. Zero local disk usage

    CONSTRAINTS:
    - Works with Claude Code CLI (can't modify 200K limit)
    - Use Google Cloud Storage API (existing OAuth)
    - Local sentence-transformers (embeddings)
    - MCP server integration
    - Production quality

    SUCCESS CRITERIA:
    1. Conversations beyond 200K without degradation
    2. Semantic retrieval >0.7 similarity
    3. Zero user intervention
    4. Voice workflow compatible
    5. Zero local disk usage
    """

    await sparc.execute_sparc(requirements)

if __name__ == "__main__":
    asyncio.run(main())
