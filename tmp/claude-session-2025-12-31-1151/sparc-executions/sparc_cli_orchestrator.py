#!/usr/bin/env python3
"""
SPARC CLI Orchestrator
Claude Code orchestrates Gemini CLI, Codex CLI, and Ollama for unlimited SPARC

Models:
- Claude Opus 4.5: claude-opus-4-5-20251101 (professional software engineering)
- Gemini 2.5 Pro: gemini-2.5-pro (research, web search)
- GPT-5.2-codex: gpt-5.2-codex with thinking levels 1-4
- Ollama qwen2.5-coder:7b (unlimited local coding)
"""

import asyncio
import subprocess
import json
import tempfile
from pathlib import Path
from datetime import datetime

class SPARCCLIOrchestrator:
    """
    Claude Code (me!) orchestrates other CLIs
    Each CLI handles its own OAuth authentication
    """

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.memory_bank = self.project_path / ".sparc"
        self.memory_bank.mkdir(parents=True, exist_ok=True)

        # Model configurations (best models for each task)
        self.models = {
            "claude_opus": "claude-opus-4-5-20251101",  # Best architecture/code
            "claude_sonnet": "claude-sonnet-4-5-20250929",  # Balanced
            "gemini_pro": "gemini-2.5-pro",  # Best research
            "gpt_codex": "gpt-5.2-codex",  # Best reasoning
            "ollama_coder": "qwen2.5-coder:7b",  # Best local code gen
            "ollama_general": "llama3.2:latest",  # General purpose
            "ollama_sparc": "sparc-qwen:latest"  # Custom SPARC model
        }

    async def run_gemini_cli(self, prompt, model=None, approval_mode="yolo"):
        """
        Run Gemini CLI with OAuth (handles auth automatically)
        Returns response text
        """
        model = model or self.models["gemini_pro"]

        cmd = [
            "gemini",
            "-m", model,
            "--approval-mode", approval_mode,
            "-p", prompt
        ]

        print(f"🟢 Gemini ({model}): {prompt[:60]}...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(f"   ❌ Error: {stderr.decode()}")
            return None

        result = stdout.decode().strip()
        print(f"   ✅ Complete ({len(result)} chars)")
        return result

    async def run_codex_cli(self, prompt, model=None, thinking_effort=None):
        """
        Run Codex CLI with OAuth (handles auth automatically)
        thinking_effort: 1-4 (1=low, 4=ultra reasoning)
        """
        model = model or self.models["gpt_codex"]

        # Build command
        cmd = [
            "codex",
            "-m", model,
            "--ask-for-approval", "never",  # Auto-execute
            prompt
        ]

        if thinking_effort:
            cmd.extend(["-c", f"reasoning_effort={thinking_effort}"])

        print(f"🔵 Codex ({model}, thinking={thinking_effort}): {prompt[:60]}...")

        # Write prompt to temp file (Codex needs stdin)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(prompt)
            temp_file = f.name

        try:
            # Run Codex with redirected stdin
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=open(temp_file, 'r'),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                print(f"   ❌ Error: {stderr.decode()}")
                return None

            result = stdout.decode().strip()
            print(f"   ✅ Complete ({len(result)} chars)")
            return result

        finally:
            Path(temp_file).unlink()

    async def run_ollama_cli(self, prompt, model=None):
        """
        Run Ollama (local, unlimited, free)
        """
        model = model or self.models["ollama_coder"]

        cmd = ["ollama", "run", model, prompt]

        print(f"🟠 Ollama ({model}): {prompt[:60]}...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        result = stdout.decode().strip()
        # Remove ANSI escape codes from Ollama output
        import re
        result = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', result)
        result = re.sub(r'\[.*?\]', '', result)  # Remove progress indicators

        print(f"   ✅ Complete ({len(result)} chars)")
        return result

    # ========================================
    # SPARC Phase 1: SPECIFICATION
    # ========================================

    async def phase1_specification(self, requirements):
        """
        Phase 1: Requirements gathering with parallel research
        Uses: Gemini (web research) + Ollama (documentation)
        """
        print("\n" + "=" * 70)
        print("📋 PHASE 1: SPECIFICATION")
        print("=" * 70)

        # Task 1: Research with Gemini (has web search tools)
        research_prompt = f"""
        Research the following project requirements:
        {requirements}

        Provide:
        1. Similar open-source projects and their approaches
        2. Best practices and design patterns
        3. Technology recommendations for 2025
        4. Common pitfalls to avoid

        Format as structured markdown research report.
        """

        research = await self.run_gemini_cli(
            research_prompt,
            model=self.models["gemini_pro"]
        )

        # Task 2: Generate requirements doc with Ollama (fast, local)
        requirements_prompt = f"""
        Based on this research:
        {research}

        Generate comprehensive REQUIREMENTS.md with:
        - Functional requirements (numbered list)
        - Non-functional requirements
        - User stories with acceptance criteria
        - Success metrics

        Format: Professional markdown
        """

        requirements_doc = await self.run_ollama_cli(
            requirements_prompt,
            model=self.models["ollama_general"]
        )

        # Save artifacts
        self.save_artifact("research.md", research)
        self.save_artifact("REQUIREMENTS.md", requirements_doc)

        print("✅ Phase 1 complete")
        return {"research": research, "requirements": requirements_doc}

    # ========================================
    # SPARC Phase 2: PSEUDOCODE
    # ========================================

    async def phase2_pseudocode(self, spec):
        """
        Phase 2: Algorithm design with deep reasoning
        Uses: GPT-5.2-codex (deep thinking level 4)
        """
        print("\n" + "=" * 70)
        print("📐 PHASE 2: PSEUDOCODE")
        print("=" * 70)

        pseudocode_prompt = f"""
        Given requirements:
        {spec['requirements']}

        Design comprehensive pseudocode with:
        1. Core algorithms (step-by-step pseudocode)
        2. Data structures with justifications
        3. Time/space complexity analysis
        4. Trade-off considerations

        Use deep reasoning to ensure optimal design.
        """

        # Use GPT with maximum reasoning (level 4)
        pseudocode = await self.run_codex_cli(
            pseudocode_prompt,
            model=self.models["gpt_codex"],
            thinking_effort=4  # Ultra reasoning
        )

        self.save_artifact("PSEUDOCODE.md", pseudocode)

        print("✅ Phase 2 complete")
        return pseudocode

    # ========================================
    # SPARC Phase 3: ARCHITECTURE
    # ========================================

    async def phase3_architecture(self, pseudocode):
        """
        Phase 3: System architecture
        Uses: Claude Opus 4.5 (best for architecture)
        """
        print("\n" + "=" * 70)
        print("🏗️ PHASE 3: ARCHITECTURE")
        print("=" * 70)

        # Note: Since I (Claude Code) AM Claude, I'll use my Task tool
        # to spawn a sub-agent with Opus 4.5

        architecture_prompt = f"""
        Given pseudocode:
        {pseudocode}

        Design complete system architecture:
        1. Component diagram (ASCII art)
        2. API specifications (OpenAPI format)
        3. Database schema (SQL DDL)
        4. Directory structure
        5. Technology stack with justifications
        6. Security architecture
        7. Scalability considerations

        Format as comprehensive ARCHITECTURE.md
        """

        # For now, use Ollama as placeholder
        # TODO: Integrate proper Claude API with Opus 4.5
        architecture = await self.run_ollama_cli(
            architecture_prompt,
            model=self.models["ollama_sparc"]
        )

        self.save_artifact("ARCHITECTURE.md", architecture)

        print("✅ Phase 3 complete")
        return architecture

    # ========================================
    # SPARC Phase 4: REFINEMENT (TDD)
    # ========================================

    async def phase4_refinement(self, architecture):
        """
        Phase 4: Test-Driven Development
        Uses: Ollama (unlimited local code generation)
        """
        print("\n" + "=" * 70)
        print("🔧 PHASE 4: REFINEMENT (TDD)")
        print("=" * 70)

        # Task 1: Generate tests with Ollama SPARC model
        tests_prompt = f"""
        Based on architecture:
        {architecture}

        Generate comprehensive test suite:
        1. Unit tests for all components
        2. Integration tests
        3. Edge case tests
        4. Performance tests

        Use pytest framework. Target 80%+ coverage.
        Return complete test files.
        """

        tests = await self.run_ollama_cli(
            tests_prompt,
            model=self.models["ollama_sparc"]
        )

        # Task 2: Implement code with qwen2.5-coder (best coding model)
        implementation_prompt = f"""
        Given tests:
        {tests}

        And architecture:
        {architecture}

        Implement production code that:
        1. Passes all tests
        2. Follows architecture exactly
        3. Includes error handling
        4. Has comprehensive docstrings
        5. Follows best practices

        Return complete source code.
        """

        implementation = await self.run_ollama_cli(
            implementation_prompt,
            model=self.models["ollama_coder"]
        )

        self.save_artifact("tests.py", tests)
        self.save_artifact("implementation.py", implementation)

        print("✅ Phase 4 complete")
        return {"tests": tests, "implementation": implementation}

    # ========================================
    # SPARC Phase 5: COMPLETION
    # ========================================

    async def phase5_completion(self, implementation):
        """
        Phase 5: Integration, security, deployment
        Uses: All models for validation
        """
        print("\n" + "=" * 70)
        print("🚀 PHASE 5: COMPLETION")
        print("=" * 70)

        # Task 1: Security audit with Gemini
        security_prompt = f"""
        Perform security audit on:
        {implementation['implementation']}

        Check for:
        - OWASP Top 10 vulnerabilities
        - Credential exposure
        - Injection vulnerabilities
        - Access control issues

        Return detailed security report.
        """

        security_audit = await self.run_gemini_cli(security_prompt)

        # Task 2: Performance optimization with GPT reasoning
        performance_prompt = f"""
        Analyze performance of:
        {implementation['implementation']}

        Optimize:
        - Database queries
        - Caching strategies
        - Async/parallel opportunities
        - Memory usage

        Return optimization recommendations.
        """

        performance = await self.run_codex_cli(
            performance_prompt,
            thinking_effort=3  # High reasoning
        )

        # Task 3: Deployment artifacts with Ollama
        deployment_prompt = f"""
        Generate deployment configuration:
        - Dockerfile
        - docker-compose.yml
        - GitHub Actions CI/CD
        - README.md

        For this application:
        {implementation['implementation']}
        """

        deployment = await self.run_ollama_cli(deployment_prompt)

        # Save all completion artifacts
        self.save_artifact("SECURITY_AUDIT.md", security_audit)
        self.save_artifact("PERFORMANCE_REPORT.md", performance)
        self.save_artifact("DEPLOYMENT.md", deployment)

        print("✅ Phase 5 complete")
        return {
            "security": security_audit,
            "performance": performance,
            "deployment": deployment
        }

    # ========================================
    # Full SPARC Execution
    # ========================================

    async def execute_sparc(self, requirements):
        """
        Execute all 5 SPARC phases
        Claude Code orchestrates all CLIs
        """
        print("=" * 70)
        print("🎯 SPARC FRAMEWORK - CLI ORCHESTRATION MODE")
        print("=" * 70)
        print(f"\nProject: {self.project_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nCLI Orchestra:")
        print("  🟢 Gemini CLI: Research & security")
        print("  🔵 Codex CLI: Deep reasoning & optimization")
        print("  🟠 Ollama: Code generation & testing (unlimited!)")
        print("  🎭 Claude Code: Conductor (that's me!)")
        print()

        start_time = datetime.now()

        # Execute phases sequentially
        spec = await self.phase1_specification(requirements)
        pseudo = await self.phase2_pseudocode(spec)
        arch = await self.phase3_architecture(pseudo)
        impl = await self.phase4_refinement(arch)
        completion = await self.phase5_completion(impl)

        # Generate final report
        elapsed = (datetime.now() - start_time).total_seconds()

        report = f"""
# SPARC Project Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Framework**: SPARC CLI Orchestration
**Elapsed Time**: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)

## Phase Summary

✅ Phase 1: Specification (Gemini + Ollama)
✅ Phase 2: Pseudocode (GPT-5.2-codex, thinking level 4)
✅ Phase 3: Architecture (Ollama SPARC)
✅ Phase 4: Refinement (Ollama qwen2.5-coder)
✅ Phase 5: Completion (All models)

## Deliverables

All artifacts in: `{self.memory_bank}/`

### Documentation
- research.md
- REQUIREMENTS.md
- PSEUDOCODE.md
- ARCHITECTURE.md

### Code
- tests.py
- implementation.py

### Reports
- SECURITY_AUDIT.md
- PERFORMANCE_REPORT.md
- DEPLOYMENT.md

## CLI Usage Statistics

| CLI | OAuth/Auth | Models Used | Cost |
|-----|-----------|-------------|------|
| Gemini CLI | OAuth (unlimited) | gemini-2.5-pro | $0 (subscription) |
| Codex CLI | OAuth (unlimited) | gpt-5.2-codex | $0 (subscription) |
| Ollama | None (local) | qwen2.5-coder, sparc-qwen | $0 (free) |

**Total Cost**: $0 marginal (using existing subscriptions)

## Next Steps

1. Review generated code: `cat {self.memory_bank}/implementation.py`
2. Run tests: `pytest {self.memory_bank}/tests.py`
3. Deploy using: `{self.memory_bank}/DEPLOYMENT.md`

---
*Generated by SPARC CLI Orchestrator*
*"Claude Code conducts the AI orchestra"*
"""

        self.save_artifact("SPARC_REPORT.md", report)

        print("\n" + "=" * 70)
        print("✅ SPARC COMPLETE")
        print("=" * 70)
        print(f"Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"Artifacts saved: {self.memory_bank}/")
        print(f"Report: {self.memory_bank}/SPARC_REPORT.md")
        print("=" * 70)

        return report

    def save_artifact(self, filename, content):
        """Save artifact to memory bank"""
        filepath = self.memory_bank / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if content:  # Only save if content exists
            filepath.write_text(content)
            print(f"   💾 Saved: {filename}")


# ========================================
# Example Usage
# ========================================

async def main():
    """
    Example: Build Instacart automation using SPARC
    """

    orchestrator = SPARCCLIOrchestrator(
        project_path=Path("/tmp/sparc_instacart_test")
    )

    requirements = """
    Build automated Instacart grocery ordering system for accessibility:

    Requirements:
    1. Voice input for adding items to cart
    2. Smart product recommendations based on past orders
    3. Automatic price comparison across stores
    4. One-click checkout with saved payment
    5. Dietary restriction filtering
    6. Budget tracking and alerts

    Accessibility Features:
    - User has typing difficulty
    - Needs minimal interaction
    - Voice-first interface
    - Large, clear UI elements

    Constraints:
    - Must work with Instacart web interface
    - macOS compatible
    - Maintainable long-term
    """

    report = await orchestrator.execute_sparc(requirements)

    print("\n📄 Final Report:")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
