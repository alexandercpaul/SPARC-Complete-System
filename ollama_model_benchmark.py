#!/usr/bin/env python3
"""
Custom Ollama Model Benchmark
Tests which model is best for different code types
"""
import requests
import time
import json
from pathlib import Path

class OllamaBenchmark:
    def __init__(self):
        self.models = [
            "qwen2.5-coder:7b",
            "sparc-qwen:latest",
            "llama3.2:latest",
            "conductor-sparc:latest"
        ]

        self.test_prompts = {
            "python": "Write a function to calculate Fibonacci numbers with memoization",
            "javascript": "Write an async function to fetch and parse JSON from an API",
            "typescript": "Create a type-safe React component with props interface",
            "rust": "Implement a thread-safe cache using Arc and Mutex",
            "sql": "Write a complex JOIN query with aggregations and subqueries",
            "bash": "Write a script to backup directories with rotation"
        }

    def test_model(self, model, language, prompt):
        """Test single model on single task"""
        start = time.time()

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60
            )

            latency = (time.time() - start) * 1000
            result = response.json()["response"]

            # Quality metrics
            has_code = "```" in result or "def " in result or "function " in result or "fn " in result
            length = len(result)

            # Check for code keywords by language
            quality_indicators = {
                "python": ["def ", "class ", "import ", "return"],
                "javascript": ["function", "const ", "async ", "=>"],
                "typescript": ["interface", "type ", "const ", ": "],
                "rust": ["fn ", "impl ", "struct ", "use "],
                "sql": ["SELECT", "JOIN", "WHERE", "GROUP BY"],
                "bash": ["#!/bin/bash", "if ", "for ", "function"]
            }

            indicator_count = sum(1 for ind in quality_indicators.get(language, []) if ind in result)

            return {
                "model": model,
                "language": language,
                "latency_ms": latency,
                "output_length": length,
                "has_code": has_code,
                "language_indicators": indicator_count,
                "quality_score": (length * 0.5) + (indicator_count * 200) if has_code else 0,
                "success": True
            }

        except Exception as e:
            return {
                "model": model,
                "language": language,
                "error": str(e),
                "quality_score": 0,
                "success": False
            }

    def run_benchmark(self):
        """Run all tests"""
        results = []

        print("=" * 80)
        print("🧪 OLLAMA MODEL BENCHMARK")
        print("=" * 80)
        print(f"Testing {len(self.models)} models on {len(self.test_prompts)} languages")
        print()

        for model in self.models:
            print(f"\n🤖 Testing {model}...")
            for language, prompt in self.test_prompts.items():
                print(f"  {language:15s}...", end=" ")
                result = self.test_model(model, language, prompt)
                results.append(result)

                if result["success"]:
                    print(f"✅ {result['latency_ms']:6.0f}ms | Score: {result['quality_score']:6.0f}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown')}")

        # Save results
        output = Path("/tmp/ollama_benchmark_results.json")
        output.write_text(json.dumps(results, indent=2))

        # Print summary
        print("\n" + "=" * 80)
        print("📊 BENCHMARK SUMMARY - BEST MODEL PER LANGUAGE")
        print("=" * 80)

        for language in self.test_prompts:
            print(f"\n{language.upper()}:")
            lang_results = [r for r in results if r["language"] == language and r["success"]]
            sorted_results = sorted(lang_results, key=lambda x: x["quality_score"], reverse=True)

            for i, r in enumerate(sorted_results, 1):
                stars = "⭐" * min(5, max(1, int(r["quality_score"] / 500)))
                medal = ["🥇", "🥈", "🥉", "  "][min(i-1, 3)]
                print(f"  {medal} {i}. {r['model']:30s} {stars:12s} {r['latency_ms']:6.0f}ms | Score: {r['quality_score']:.0f}")

        # Overall winner
        print("\n" + "=" * 80)
        print("🏆 OVERALL WINNER (Average Quality Score)")
        print("=" * 80)

        model_scores = {}
        for model in self.models:
            model_results = [r for r in results if r["model"] == model and r["success"]]
            if model_results:
                avg_score = sum(r["quality_score"] for r in model_results) / len(model_results)
                avg_latency = sum(r["latency_ms"] for r in model_results) / len(model_results)
                model_scores[model] = {"score": avg_score, "latency": avg_latency}

        sorted_models = sorted(model_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        for i, (model, stats) in enumerate(sorted_models, 1):
            medal = ["🥇", "🥈", "🥉", "  "][min(i-1, 3)]
            stars = "⭐" * min(5, max(1, int(stats["score"] / 500)))
            print(f"{medal} {i}. {model:30s} {stars:12s} Avg: {stats['latency']:6.0f}ms | Score: {stats['score']:.0f}")

        print("\n" + "=" * 80)
        print(f"📁 Full results saved to: {output}")
        print("=" * 80)
        return results

if __name__ == "__main__":
    benchmark = OllamaBenchmark()
    results = benchmark.run_benchmark()

    print("\n💡 Recommendations:")
    print("  - Use the top-ranked model for each language")
    print("  - qwen2.5-coder:7b should perform best overall")
    print("  - sparc-qwen best for planning/architecture")
    print("  - llama3.2 fastest but lower quality")
