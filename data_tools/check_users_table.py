from supabase_handler import SupabaseHandler

def check_users_table():
    handler = SupabaseHandler()
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    try:
        # Check if users table exists by selecting one row
        res = handler.client.table("users").select("*").limit(1).execute()
        print("Users table exists and is accessible.")
    except Exception as e:
        print(f"Users table might not exist or is inaccessible: {e}")

if __name__ == "__main__":
    check_users_table()
