import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions import supabase as handler

def cleanup_and_repopulate():
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    categories = ["tenses", "prepositions"]
    
    for cat in categories:
        print(f"Cleaning up category: {cat}...")
        res = handler._safe_execute(handler.client.table("questions").delete().eq("category", cat))
        if res:
            print(f"  Successfully deleted old {cat} questions.")
        else:
            print(f"  Failed to delete or no questions found for {cat}.")

    # Now repopulate using the existing population scripts (or just call their logic)
    # I'll just run the population scripts via subprocess for simplicity if they are already there
    import subprocess
    
    print("\nRepopulating Tenses...")
    subprocess.run(["python", "data_tools/populate_tenses.py"])
    
    print("\nRepopulating Prepositions...")
    subprocess.run(["python", "data_tools/populate_prepositions.py"])
    
    print("\nCleanup and Repopulation complete!")

if __name__ == "__main__":
    cleanup_and_repopulate()
