from supabase_handler import SupabaseHandler

def check_counts():
    handler = SupabaseHandler()
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    types = ['aptitude', 'lr', 'va']
    diffs = ['easy', 'medium', 'hard']
    
    print("Checking question counts in Supabase...")
    for t in types:
        for d in diffs:
            res = handler.client.table("questions").select("*", count="exact").eq("type", t).eq("difficulty", d).execute()
            count = res.count if res else 0
            print(f"Type: {t:10} | Difficulty: {d:8} | Count: {count}")

if __name__ == "__main__":
    check_counts()
