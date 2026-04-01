import os
from supabase import create_client, Client
from supabase.client import ClientOptions
from gotrue import SyncSupportedStorage
from flask import session
from dotenv import load_dotenv

load_dotenv()

class FlaskSessionStorage(SyncSupportedStorage):
    """
    Custom storage for Supabase auth to persist JWT in Flask session cookies.
    """
    def get_item(self, key: str) -> str or None:
        return session.get(key)

    def set_item(self, key: str, value: str) -> None:
        session[key] = value

    def remove_item(self, key: str) -> None:
        session.pop(key, None)

class SupabaseHandler:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key or "your_supabase" in url:
            self.client = None
            print("Warning: Supabase credentials not configured.")
        else:
            self.client: Client = create_client(
                url, 
                key,
                options=ClientOptions(
                    storage=FlaskSessionStorage(),
                    flow_type="pkce"
                )
            )

    def sign_up(self, email, password):
        if not self.client: return None
        return self.client.auth.sign_up({"email": email, "password": password})

    def sign_in(self, email, password):
        if not self.client: return None
        return self.client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        if not self.client: return
        self.client.auth.sign_out()
        session.clear()

    def get_user(self):
        if not self.client: return None
        try:
            return self.client.auth.get_user()
        except:
            return None

    def save_session_result(self, user_id, session_data, feedbacks):
        """
        Saves a completed practice session and its associated feedback items.
        """
        if not self.client: return
        
        # 1. Insert the main session
        session_row = {
            "user_id": user_id,
            "type": session_data.get('type'),
            "category": session_data.get('category'),
            "difficulty": session_data.get('difficulty'),
            "score": session_data.get('score'),
        }
        
        res = self.client.table("sessions").insert(session_row).execute()
        if res.data:
            session_id = res.data[0]['id']
            # 2. Insert feedback items
            feedback_rows = []
            for fb in feedbacks:
                feedback_rows.append({
                    "session_id": session_id,
                    "question": fb.get('question'),
                    "score": fb.get('score', 0),
                    "strength": fb.get('strength', ''),
                    "weakness": fb.get('weakness', ''),
                    "suggestion": fb.get('suggestion', '')
                })
            
            if feedback_rows:
                self.client.table("session_feedback").insert(feedback_rows).execute()

    def get_dashboard_data(self, user_id):
        """
        Fetches session history and aggregates stats for the dashboard.
        """
        if not self.client: return {}

        # Get last 20 sessions
        sessions = self.client.table("sessions")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()

        # Get feedback to analyze weak areas
        feedbacks = self.client.table("session_feedback")\
            .select("weakness, score")\
            .execute() # In a real app, join with user's sessions

        return {
            "sessions": sessions.data,
            "feedbacks": feedbacks.data
        }
