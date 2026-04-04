from supabase_handler import SupabaseHandler

def test_query():
    handler = SupabaseHandler()
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    q_type = 'aptitude'
    difficulty = 'Easy'
    limit = 10
    
    print(f"Testing random fetch for {q_type} / {difficulty}...")
    
    # Simulate current logic
    target_type = q_type.lower()
    target_diff = difficulty.lower() if difficulty else None
    
    query = handler.client.table("questions").select("*", count="exact").eq("type", target_type)
    if target_diff and target_diff != 'all':
        query = query.eq("difficulty", target_diff)
    
    # 1. Count
    count_res = handler._safe_execute(query.limit(1))
    total_count = count_res.count if count_res else 0
    print(f"Total count: {total_count}")
    
    if total_count > 0:
        import random
        random_offset = random.randint(0, max(0, total_count - limit))
        print(f"Random offset: {random_offset}")
        
        # 2. Fetch using DIFFERENT builder instance or reset?
        # Re-build for now to ensure it works
        query2 = handler.client.table("questions").select("*").eq("type", target_type)
        if target_diff and target_diff != 'all':
            query2 = query2.eq("difficulty", target_diff)
        
        res = handler._safe_execute(query2.range(random_offset, random_offset + limit - 1))
        if res and res.data:
            print(f"Success! Fetched {len(res.data)} questions.")
        else:
            print(f"Failed to fetch with offset. Response: {res.data if res else 'None'}")

if __name__ == "__main__":
    test_query()
