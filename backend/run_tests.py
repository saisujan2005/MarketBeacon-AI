"""
Minimal test runner.

The project does not currently depend on pytest, and this hardening pass avoids
adding new dependencies. These test modules use plain `assert` and `test_*`
function names, so they are pytest-compatible: once pytest is installed,
`pytest backend/tests` will work unchanged.

Usage (from the backend/ directory):
    python run_tests.py
    python run_tests.py test_alerts          # run one module
"""

import importlib
import sys
import traceback

TEST_MODULES = [
    "tests.test_config_and_uploads",
    "tests.test_route_protection",
    "tests.test_alerts",
    "tests.test_tenant_isolation",
]


def run_module(module_name):
    passed, failed = 0, []
    try:
        module = importlib.import_module(module_name)
    except Exception:
        print(f"\n!! Could not import {module_name}")
        traceback.print_exc()
        return 0, [(module_name, "import error")]

    print(f"\n=== {module_name} ===")
    for name in sorted(dir(module)):
        if not name.startswith("test_"):
            continue
        fn = getattr(module, name)
        if not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed.append((f"{module_name}.{name}", str(e)))
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            failed.append((f"{module_name}.{name}", f"{type(e).__name__}: {e}"))
    return passed, failed


def main():
    selected = sys.argv[1:]
    modules = [m for m in TEST_MODULES if not selected or any(s in m for s in selected)]

    total_passed, all_failed = 0, []
    for m in modules:
        p, f = run_module(m)
        total_passed += p
        all_failed.extend(f)

    print("\n" + "=" * 60)
    print(f"PASSED: {total_passed}   FAILED: {len(all_failed)}")
    if all_failed:
        print("\nFailures:")
        for name, err in all_failed:
            print(f"  - {name}: {err}")
    print("=" * 60)
    return 1 if all_failed else 0


if __name__ == "__main__":
    sys.exit(main())
