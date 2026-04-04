import sys
import os

# Ensure the project root is in the path (since we are in data_tools/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from routes.aptitude import resolve_answer_letter
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

test_cases = [
    {
        "name": "Letter Match (B)",
        "question": {"options": ["1", "2", "3", "4"], "answer": "B"},
        "expected": "B"
    },
    {
        "name": "Full Text Match ($112)",
        "question": {"options": ["$112", "$110", "$108", "$102"], "answer": "$112"},
        "expected": "A"
    },
    {
        "name": "Numeric Text Match (25)",
        "question": {"options": ["20", "22", "25", "30"], "answer": "25"},
        "expected": "C"
    },
    {
        "name": "Prefix Match (A. 1 day)",
        "question": {"options": ["1 day", "5 days", "10 days", "20 days"], "answer": "A. 1 day"},
        "expected": "A"
    },
    {
        "name": "Fallback check",
        "question": {"options": ["X", "Y", "Z", "W"], "answer": "Missing"},
        "expected": "A"
    }
]

print("--- Aptitude Answer Resolver Test ---")
failed = 0
for case in test_cases:
    result = resolve_answer_letter(case["question"])
    if result == case["expected"]:
        print(f"[OK] {case['name']}: Resolved to {result}")
    else:
        print(f"[FAIL] {case['name']}: Expected {case['expected']}, got {result}")
        failed += 1

if failed == 0:
    print("\n✅ ALL TESTS PASSED! 'Option A' bias is eliminated.")
else:
    print(f"\n❌ {failed} TESTS FAILED.")
