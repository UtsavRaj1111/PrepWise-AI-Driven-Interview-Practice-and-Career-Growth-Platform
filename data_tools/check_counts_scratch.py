import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions import supabase as handler

def check_counts():
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    categories = ["tenses", "prepositions", "error_correction", "para_jumbles", "sentence_completion"]
    difficulties = ["easy", "medium", "hard"]
    
    print(f"{'Category':<15} | {'Difficulty':<10} | {'Count':<5}")
    print("-" * 35)
    
    for cat in categories:
        for diff in difficulties:
            res = handler._safe_execute(
                handler.client.table("questions")
                .select("*", count="exact")
                .eq("category", cat)
                .eq("difficulty", diff)
                .limit(1)
            )
            count = res.count if res else 0
            print(f"{cat:<15} | {diff:<10} | {count:<5}")

if __name__ == "__main__":
    check_counts()
