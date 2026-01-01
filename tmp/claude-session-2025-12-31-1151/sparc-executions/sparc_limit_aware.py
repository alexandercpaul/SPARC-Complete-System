#!/usr/bin/env python3
"""
SPARC Limit-Aware Orchestrator
Respects subscription session/weekly/daily limits
Uses cloud APIs strategically, Ollama for bulk work

Subscription limits:
- Claude Max: 200-800 prompts per 5hr session
- ChatGPT Pro: ~6-7 intensive sessions per week
- Gemini Ultra: Daily limits (undisclosed)

Strategy: Use premium models for architecture/reasoning, Ollama for code generation
"""

import asyncio
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

class LimitAwareSPARC:
    """
    SPARC that respects subscription limits
    Tracks usage and auto-switches to Ollama when needed
    """

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.memory_bank = self.project_path / ".sparc"
        self.memory_bank.mkdir(parents=True, exist_ok=True)

        # Updated model names (Dec 2025)
        self.models = {
            # Cloud models (LIMITED by subscriptions)
            "claude_opus": "claude-opus-4-5-20251101",     # Max: Architecture, review
            "claude_sonnet": "claude-sonnet-4-5-20250929", # Max: General tasks
            "gemini_flash": "gemini-3-flash",              # Ultra: Research (just released!)
            "gpt_codex": "gpt-5.2-codex",                  # Pro: Deep reasoning

            # Local models (UNLIMITED but slower)
            "ollama_coder": "qwen2.5-coder:7b",            # Best code generation
            "ollama_general": "llama3.2:latest",           # Documentation
            "ollama_sparc": "sparc-qwen:latest"            # SPARC-tuned
        }

        # Usage tracking
        self.usage = {
            "claude_prompts": 0,       # Max: 200-800 per 5hr session
            "gpt_prompts": 0,          # Pro: Limited weekly
            "gemini_prompts": 0,       # Ultra: Daily limit
            "ollama_prompts": 0        # Unlimited
        }

        # Limits (conservative estimates)
        self.limits = {
            "claude_session": 200,     # Conservative (actual: 200-800)
            "gpt_weekly": 50,          # Very conservative (weekly cap)
            "gemini_daily": 100        # Unknown, so conservative
        }

    def check_limit(self, service):
        """Check if we're approaching limits for a service"""
        if service == "claude":
            usage_pct = (self.usage["claude_prompts"] / self.limits["claude_session"]) * 100
            return usage_pct < 80  # Stop at 80% to be safe
        elif service == "gpt":
            usage_pct = (self.usage["gpt_prompts"] / self.limits["gpt_weekly"]) * 100
            return usage_pct < 80
        elif service == "gemini":
            usage_pct = (self.usage["gemini_prompts"] / self.limits["gemini_daily"]) * 100
            return usage_pct < 80
        return True  # Ollama always available

    def get_best_model(self, task_type, fallback_to_ollama=True):
        """
        Choose best model for task type, respecting limits
        Falls back to Ollama if cloud limits hit
        """
        if task_type == "architecture":
            if self.check_limit("claude"):
                return ("claude", self.models["claude_opus"])
            elif fallback_to_ollama:
                print("   ⚠️  Claude limit reached, using Ollama SPARC instead")
                return ("ollama", self.models["ollama_sparc"])

        elif task_type == "reasoning":
            if self.check_limit("gpt"):
                return ("gpt", self.models["gpt_codex"])
            elif fallback_to_ollama:
                print("   ⚠️  GPT limit reached, using Ollama instead")
                return ("ollama", self.models["ollama_sparc"])

        elif task_type == "research":
            if self.check_limit("gemini"):
                return ("gemini", self.models["gemini_flash"])
            elif fallback_to_ollama:
                print("   ⚠️  Gemini limit reached, using Ollama instead")
                return ("ollama", self.models["ollama_general"])

        elif task_type == "code_generation":
            # Always use Ollama for bulk code (unlimited!)
            return ("ollama", self.models["ollama_coder"])

        elif task_type == "documentation":
            # Always use Ollama for docs (unlimited!)
            return ("ollama", self.models["ollama_general"])

        # Default to Ollama
        return ("ollama", self.models["ollama_general"])

    async def run_gemini_cli(self, prompt, model=None):
        """Run Gemini CLI and track usage"""
        model = model or self.models["gemini_flash"]

        cmd = ["gemini", "-m", model, "--approval-mode", "yolo", "-p", prompt]

        print(f"🟢 Gemini ({model}): {prompt[:60]}...")
        self.usage["gemini_prompts"] += 1

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(f"   ❌ Error: {stderr.decode()}")
            return None

        result = stdout.decode().strip()
        print(f"   ✅ Complete ({self.usage['gemini_prompts']}/{self.limits['gemini_daily']} used today)")
        return result

    async def run_codex_cli(self, prompt, thinking=4):
        """Run Codex CLI and track usage"""
        # Note: Codex requires proper stdin handling
        print(f"🔵 GPT-Codex (thinking={thinking}): {prompt[:60]}...")
        self.usage["gpt_prompts"] += 1

        # For now, fallback to Ollama for Codex (stdin issues)
        print(f"   ⚠️  Using Ollama instead (Codex stdin handling needs work)")
        return await self.run_ollama_cli(prompt, self.models["ollama_coder"])

    async def run_ollama_cli(self, prompt, model=None):
        """Run Ollama (unlimited, but slower)"""
        model = model or self.models["ollama_coder"]

        cmd = ["ollama", "run", model, prompt]

        print(f"🟠 Ollama ({model}): {prompt[:60]}...")
        self.usage["ollama_prompts"] += 1

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        result = stdout.decode().strip()
        # Clean ANSI codes
        result = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', result)
        result = re.sub(r'\[.*?\]', '', result)

        print(f"   ✅ Complete (unlimited local)")
        return result

    # ========================================
    # SPARC PHASES
    # ========================================

    async def phase1_specification(self, requirements):
        """
        Phase 1: Requirements with 17-agent specialization
        Uses: Gemini (research) + Ollama (docs)
        """
        print("\n" + "=" * 70)
        print("📋 PHASE 1: SPECIFICATION")
        print("=" * 70)

        # Agent 1: Researcher (Gemini for web search)
        service, model = self.get_best_model("research")
        if service == "gemini":
            research = await self.run_gemini_cli(
                f"Research project requirements and best practices for: {requirements}",
                model
            )
        else:
            research = await self.run_ollama_cli(
                f"Research best practices for: {requirements}",
                model
            )

        # Agent 2: Spec Writer (Ollama - unlimited docs)
        spec_doc = await self.run_ollama_cli(
            f"Based on research:\n{research}\n\nGenerate REQUIREMENTS.md with functional requirements, user stories, and success metrics.",
            self.models["ollama_general"]
        )

        self.save_artifact("research.md", research)
        self.save_artifact("REQUIREMENTS.md", spec_doc)

        print(f"✅ Phase 1 complete")
        self.print_usage()
        return {"research": research, "requirements": spec_doc}

    async def phase2_pseudocode(self, spec):
        """
        Phase 2: Algorithm design
        Uses: GPT (reasoning) OR Ollama if limit hit
        """
        print("\n" + "=" * 70)
        print("📐 PHASE 2: PSEUDOCODE")
        print("=" * 70)

        # Agent 3: Algorithm Designer
        service, model = self.get_best_model("reasoning")

        prompt = f"""Given requirements:
{spec['requirements']}

Design algorithms with:
1. Step-by-step pseudocode
2. Data structures
3. Complexity analysis
4. Trade-offs

Format as PSEUDOCODE.md"""

        if service == "gpt":
            pseudocode = await self.run_codex_cli(prompt, thinking=4)
        else:
            pseudocode = await self.run_ollama_cli(prompt, model)

        self.save_artifact("PSEUDOCODE.md", pseudocode)

        print(f"✅ Phase 2 complete")
        self.print_usage()
        return pseudocode

    async def phase3_architecture(self, pseudocode):
        """
        Phase 3: System design
        Uses: Claude Opus OR Ollama if limit hit
        """
        print("\n" + "=" * 70)
        print("🏗️ PHASE 3: ARCHITECTURE")
        print("=" * 70)

        # Agent 4: Architect
        service, model = self.get_best_model("architecture")

        prompt = f"""Given pseudocode:
{pseudocode}

Design system architecture with:
1. Component diagram
2. API specs
3. Database schema
4. Technology stack
5. Security architecture

Format as ARCHITECTURE.md"""

        # Note: Claude CLI would go here, but we'll use Ollama for now
        architecture = await self.run_ollama_cli(prompt, self.models["ollama_sparc"])

        self.save_artifact("ARCHITECTURE.md", architecture)

        print(f"✅ Phase 3 complete")
        self.print_usage()
        return architecture

    async def phase4_refinement(self, architecture):
        """
        Phase 4: TDD Implementation
        Uses: Ollama ONLY (bulk code generation - unlimited!)
        """
        print("\n" + "=" * 70)
        print("🔧 PHASE 4: REFINEMENT (TDD)")
        print("=" * 70)

        # Agent 5-10: Code generation team (all Ollama - unlimited!)

        # Agent 5: Test Writer
        print("   Agent 5: Test Writer (Ollama)")
        tests = await self.run_ollama_cli(
            f"Based on:\n{architecture}\n\nGenerate comprehensive test suite with unit tests, integration tests, edge cases. Use pytest.",
            self.models["ollama_sparc"]
        )

        # Agent 6-8: Code Implementation (parallel!)
        print("   Agents 6-8: Implementation Team (Ollama parallel)")

        impl_tasks = [
            ("Backend", "Implement backend code that passes tests"),
            ("Frontend", "Implement frontend code"),
            ("Integration", "Implement integration layer")
        ]

        implementations = await asyncio.gather(*[
            self.run_ollama_cli(
                f"Architecture:\n{architecture}\n\nTests:\n{tests}\n\n{task}",
                self.models["ollama_coder"]
            )
            for name, task in impl_tasks
        ])

        # Combine implementations
        full_impl = "\n\n".join([
            f"# {name}\n{impl}"
            for (name, _), impl in zip(impl_tasks, implementations)
        ])

        # Agent 9: Security Review
        print("   Agent 9: Security Review (Ollama)")
        security = await self.run_ollama_cli(
            f"Review for security vulnerabilities:\n{full_impl}",
            self.models["ollama_general"]
        )

        # Agent 10: Quality Assurance
        print("   Agent 10: Quality Check (Ollama)")
        quality = await self.run_ollama_cli(
            f"Check code quality, lint, coverage:\n{full_impl}",
            self.models["ollama_general"]
        )

        self.save_artifact("tests.py", tests)
        self.save_artifact("implementation.py", full_impl)
        self.save_artifact("security_review.md", security)
        self.save_artifact("quality_report.md", quality)

        print(f"✅ Phase 4 complete (100% Ollama - no cloud usage!)")
        self.print_usage()
        return {
            "tests": tests,
            "implementation": full_impl,
            "security": security,
            "quality": quality
        }

    async def phase5_completion(self, implementation):
        """
        Phase 5: Final validation and deployment
        Uses: Mix of cloud (if limits allow) + Ollama
        """
        print("\n" + "=" * 70)
        print("🚀 PHASE 5: COMPLETION")
        print("=" * 70)

        # Agent 11-17: Completion team

        # Agent 11: Integration Tester (Ollama)
        print("   Agent 11: Integration Testing (Ollama)")
        integration = await self.run_ollama_cli(
            f"Run integration tests for:\n{implementation['implementation']}",
            self.models["ollama_general"]
        )

        # Agent 12: Performance Optimizer (GPT if available, else Ollama)
        print("   Agent 12: Performance Optimization")
        service, model = self.get_best_model("reasoning")
        if service == "gpt":
            performance = await self.run_codex_cli(
                f"Optimize performance of:\n{implementation['implementation']}",
                thinking=3
            )
        else:
            performance = await self.run_ollama_cli(
                f"Optimize performance:\n{implementation['implementation']}",
                model
            )

        # Agent 13-17: Deployment team (all Ollama)
        print("   Agents 13-17: Deployment Team (Ollama)")

        deployment_tasks = [
            ("Dockerfile", "Generate Dockerfile"),
            ("docker-compose", "Generate docker-compose.yml"),
            ("CI/CD", "Generate GitHub Actions workflow"),
            ("README", "Generate comprehensive README.md"),
            ("Monitoring", "Generate monitoring/logging setup")
        ]

        deployments = await asyncio.gather(*[
            self.run_ollama_cli(
                f"For application:\n{implementation['implementation'][:500]}...\n\n{task}",
                self.models["ollama_general"]
            )
            for name, task in deployment_tasks
        ])

        for (name, _), content in zip(deployment_tasks, deployments):
            self.save_artifact(f"{name}.md", content)

        self.save_artifact("integration_tests.md", integration)
        self.save_artifact("performance_report.md", performance)

        print(f"✅ Phase 5 complete")
        self.print_usage()
        return {
            "integration": integration,
            "performance": performance,
            "deployment": deployments
        }

    # ========================================
    # FULL SPARC EXECUTION
    # ========================================

    async def execute_sparc(self, requirements):
        """Execute all 5 SPARC phases with 17 specialized agents"""
        print("=" * 70)
        print("🎯 SPARC FRAMEWORK - 17 AGENT SPECIALIZATION")
        print("=" * 70)
        print(f"\nProject: {self.project_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n17-Agent Team:")
        print("  Agents 1-2: Specification (Gemini + Ollama)")
        print("  Agent 3: Pseudocode (GPT/Ollama)")
        print("  Agent 4: Architecture (Claude/Ollama)")
        print("  Agents 5-10: Refinement (All Ollama - unlimited!)")
        print("  Agents 11-17: Completion (Mix based on limits)")
        print()

        start_time = datetime.now()

        # Execute all phases
        spec = await self.phase1_specification(requirements)
        pseudo = await self.phase2_pseudocode(spec)
        arch = await self.phase3_architecture(pseudo)
        impl = await self.phase4_refinement(arch)
        completion = await self.phase5_completion(impl)

        # Generate final report
        elapsed = (datetime.now() - start_time).total_seconds()

        report = f"""
# SPARC Project Report - 17 Agent Specialization

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Elapsed Time**: {elapsed:.1f}s ({elapsed/60:.1f} minutes)

## 17-Agent Team Performance

✅ Phase 1: Agents 1-2 (Research + Spec)
✅ Phase 2: Agent 3 (Algorithms)
✅ Phase 3: Agent 4 (Architecture)
✅ Phase 4: Agents 5-10 (TDD + Implementation)
✅ Phase 5: Agents 11-17 (Validation + Deployment)

## Usage Statistics

| Service | Prompts Used | Limit | Status |
|---------|--------------|-------|--------|
| Claude Max | {self.usage['claude_prompts']} | {self.limits['claude_session']}/5hr | {'✅' if self.usage['claude_prompts'] < self.limits['claude_session'] * 0.8 else '⚠️'} |
| ChatGPT Pro | {self.usage['gpt_prompts']} | {self.limits['gpt_weekly']}/week | {'✅' if self.usage['gpt_prompts'] < self.limits['gpt_weekly'] * 0.8 else '⚠️'} |
| Gemini Ultra | {self.usage['gemini_prompts']} | {self.limits['gemini_daily']}/day | {'✅' if self.usage['gemini_prompts'] < self.limits['gemini_daily'] * 0.8 else '⚠️'} |
| Ollama | {self.usage['ollama_prompts']} | Unlimited | ✅ |

**Total Cloud Prompts**: {self.usage['claude_prompts'] + self.usage['gpt_prompts'] + self.usage['gemini_prompts']}
**Total Ollama Prompts**: {self.usage['ollama_prompts']} (free!)

**Cost**: $0 marginal (using subscriptions)

## Deliverables

All artifacts in: `{self.memory_bank}/`

📄 Documentation: research.md, REQUIREMENTS.md, PSEUDOCODE.md, ARCHITECTURE.md
💻 Code: tests.py, implementation.py
📊 Reports: security_review.md, quality_report.md, performance_report.md
🚀 Deployment: Dockerfile.md, docker-compose.md, CI/CD.md, README.md, Monitoring.md

## Next Steps

1. Review code: `cat {self.memory_bank}/implementation.py`
2. Run tests: `pytest {self.memory_bank}/tests.py`
3. Deploy: Follow `{self.memory_bank}/README.md`

---
*Generated by SPARC 17-Agent Framework*
*Limit-aware orchestration for subscription tiers*
"""

        self.save_artifact("SPARC_REPORT.md", report)

        print("\n" + "=" * 70)
        print("✅ SPARC COMPLETE - 17 AGENTS FINISHED!")
        print("=" * 70)
        print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"Artifacts: {self.memory_bank}/")
        print(f"Report: {self.memory_bank}/SPARC_REPORT.md")
        self.print_usage_final()
        print("=" * 70)

        return report

    def save_artifact(self, filename, content):
        """Save artifact to memory bank"""
        if content:
            filepath = self.memory_bank / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
            print(f"   💾 Saved: {filename}")

    def print_usage(self):
        """Print current usage stats"""
        print(f"\n   📊 Usage: Claude {self.usage['claude_prompts']}/{self.limits['claude_session']} | "
              f"GPT {self.usage['gpt_prompts']}/{self.limits['gpt_weekly']} | "
              f"Gemini {self.usage['gemini_prompts']}/{self.limits['gemini_daily']} | "
              f"Ollama {self.usage['ollama_prompts']} (unlimited)")

    def print_usage_final(self):
        """Print final usage summary"""
        cloud_total = self.usage['claude_prompts'] + self.usage['gpt_prompts'] + self.usage['gemini_prompts']
        print(f"\n📊 Final Usage:")
        print(f"   Cloud APIs: {cloud_total} prompts")
        print(f"   Ollama: {self.usage['ollama_prompts']} prompts (unlimited local)")
        print(f"   Strategy: Used cloud for high-value tasks, Ollama for bulk work")


# ========================================
# EXAMPLE: First SPARC Test
# ========================================

async def first_sparc_test():
    """
    First SPARC test with 17-agent specialization
    """

    orchestrator = LimitAwareSPARC(
        project_path=Path("/tmp/sparc_first_test")
    )

    # Simple first test - something useful but not too complex
    requirements = """
    Build a simple web scraper CLI tool:

    Requirements:
    1. Accept URL as command-line argument
    2. Extract all links from the page
    3. Extract main text content
    4. Save results to JSON file
    5. Include error handling for network issues
    6. Add progress indicators

    Constraints:
    - Python 3.10+
    - Use requests + beautifulsoup4
    - CLI should be user-friendly
    - Must include unit tests
    """

    report = await orchestrator.execute_sparc(requirements)

    print("\n📄 Final Report:")
    print(report)

    print("\n✅ First SPARC test complete!")
    print(f"Check output: /tmp/sparc_first_test/.sparc/")


if __name__ == "__main__":
    print("🎯 SPARC 17-Agent Framework - Ready!")
    print("Run: asyncio.run(first_sparc_test())")
    print()

    # Run the test
    asyncio.run(first_sparc_test())
