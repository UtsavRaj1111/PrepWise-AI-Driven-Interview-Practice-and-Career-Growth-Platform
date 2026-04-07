from supabase import create_client
from supabase_handler import SupabaseHandler
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ✅ REAL Supabase client (for AUTH)
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Your custom handler (for DB)
supabase = SupabaseHandler(supabase_client)