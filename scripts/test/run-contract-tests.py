#!/usr/bin/env python3
"""
Contract test runner for setup validation
Executes all contract tests and provides detailed reporting
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class ContractTestRunner:
    """Runs contract tests with detailed reporting"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.backend_dir = self.project_root / "backend"
        self.test_dir = self.backend_dir / "tests" / "contract"

    def check_prerequisites(self) -> bool:
        """Check if test environment is ready"""
        print("🔍 Checking prerequisites...")

        # Check test directory exists
        if not self.test_dir.exists():
            print(f"❌ Contract test directory not found: {self.test_dir}")
            return False

        # Check pytest is available
        try:
            subprocess.run(["pytest", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ pytest not found. Install with: pip install pytest")
            return False

        print("✅ Prerequisites check passed")
        return True

    def run_tests(self, verbose: bool = True, parallel: bool = False) -> Dict[str, Any]:
        """Run all contract tests"""
        print("\n🧪 Running contract tests...")

        cmd = ["pytest", str(self.test_dir), "--tb=short", "-v" if verbose else "-q"]

        if parallel:
            cmd.extend(["-n", "auto"])

        # Add JSON reporting
        json_report = self.backend_dir / "test-results.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Parse results
            test_results = self._parse_results(result, duration, json_report)

            return test_results

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out after 5 minutes",
                "duration": 300
            }

    def _parse_results(self, result: subprocess.CompletedProcess,
                      duration: float, json_report: Path) -> Dict[str, Any]:
        """Parse test results from pytest output"""

        # Try to load JSON report
        json_data = None
        if json_report.exists():
            try:
                with open(json_report) as f:
                    json_data = json.load(f)
            except Exception:
                pass

        # Basic result parsing
        return_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr

        # Count test results from output
        passed = stdout.count(" PASSED")
        failed = stdout.count(" FAILED")
        errors = stdout.count(" ERROR")

        success = return_code == 0

        test_data = {
            "success": success,
            "return_code": return_code,
            "duration": duration,
            "counts": {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "total": passed + failed + errors
            },
            "stdout": stdout,
            "stderr": stderr
        }

        if json_data:
            test_data["detailed_results"] = json_data

        return test_data

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print test results summary"""
        print(f"\n📊 Contract Test Results")
        print("=" * 40)

        if results["success"]:
            print("✅ All contract tests PASSED")
        else:
            print("❌ Some contract tests FAILED")

        counts = results.get("counts", {})
        print(f"📈 Passed: {counts.get('passed', 0)}")
        print(f"💥 Failed: {counts.get('failed', 0)}")
        print(f"⚠️  Errors: {counts.get('errors', 0)}")
        print(f"⏱️  Duration: {results.get('duration', 0):.2f}s")

        if not results["success"] and results.get("stderr"):
            print(f"\n🔍 Error Details:")
            print(results["stderr"][:500])  # First 500 chars


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Run contract tests")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--json-output", help="Save results to JSON file")

    args = parser.parse_args()

    runner = ContractTestRunner()

    if not runner.check_prerequisites():
        sys.exit(1)

    results = runner.run_tests(verbose=not args.quiet, parallel=args.parallel)

    runner.print_summary(results)

    # Save JSON output if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.json_output}")

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()