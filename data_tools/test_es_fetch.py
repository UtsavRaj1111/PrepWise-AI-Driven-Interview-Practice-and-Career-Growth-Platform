import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions import supabase as handler

def verify():
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    difficulties = ["easy", "medium", "hard"]
    for diff in difficulties:
        print(f"Checking {diff} questions...")
        res = handler.get_random_questions("va", difficulty=diff, category="error-spotting", limit=5)
        print(f"  Fetched {len(res)} {diff} questions.")
        if res:
            for i, q in enumerate(res):
                print(f"  Q{i+1}: {q.get('question')[:50]}...")
                print(f"     Answer: {q.get('answer')}")

if __name__ == "__main__":
    verify()
