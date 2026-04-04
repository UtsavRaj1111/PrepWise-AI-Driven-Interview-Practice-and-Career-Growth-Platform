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
    def __init__(self, client):
        """
    Initialize with already created Supabase client
    """
        self.client = client
       
    def sign_up(self, email, password):
        """
        Signs up a new user. Record creation is deferred to login flow for RLS stability.
        """
        if not self.client: return None
        res = self.client.auth.sign_up({"email": email, "password": password})
        if res and res.user:
            # OPTIONAL: Initial record creation. Might fail due to RLS before session is ready.
            # Lazy initialization on first login will handle this properly.
            user_data = {"id": res.user.id, "email": email}
            self._safe_execute(self.client.table("users").insert(user_data))
        return res

    def sign_in(self, email, password):
        if not self.client: return None
        try:
            return self.client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            print(f"AUTH ERROR: {e}")
            return None

    def sign_out(self):
        if not self.client: return
        self.client.auth.sign_out()
        session.clear()

    def get_user(self, jwt=None):
        """
        Retrieves the current user. If a JWT is provided, extracts user from the token.
        """
        if not self.client: return None
        try:
            if jwt:
                return self.client.auth.get_user(jwt)
            return self.client.auth.get_user()
        except:
            return None

    def get_session(self):
        """
        Retrieves the current auth session including access_token and refresh_token.
        """
        if not self.client: return None
        try:
            return self.client.auth.get_session()
        except:
            return None

    def _safe_execute(self, query):
        """
        Helper to execute Supabase queries and catch connection/network errors.
        """
        if not self.client: return None
        try:
            return query.execute()
        except Exception as e:
            # Catch httpx.ConnectError, DNS lookup failures, etc.
            print(f"SUPABASE CONNECTION ERROR: {e}")
            return None

    def save_session_result(self, user_id, session_data, feedbacks):
        session_row = {
            "user_id": user_id,
           
        }
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
        
        res = self._safe_execute(self.client.table("sessions").insert(session_row))
        if res and res.data:
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
                self._safe_execute(self.client.table("session_feedback").insert(feedback_rows))

    def get_dashboard_data(self, user_id):
        """
        Fetches session history and aggregates stats for the dashboard.
        """
        if not self.client: return {"sessions": [], "feedbacks": []}

        try:
            # Get last 20 sessions
            sessions = self._safe_execute(
                self.client.table("sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(20)
            )

            # Get feedback to analyze weak areas
            feedbacks = self._safe_execute(
                self.client.table("session_feedback")
                .select("weakness, score")
            )

            return {
                "sessions": sessions.data if sessions else [],
                "feedbacks": feedbacks.data if feedbacks else []
            }
        except Exception as e:
            print(f"Supabase Dashboard Data Error: {e}")
            return {"sessions": [], "feedbacks": []}

    def get_random_questions(self, q_type, difficulty=None, limit=10):
        """
        Fetches random questions from the 'questions' table based on type and difficulty.
        Uses a random offset to sample from the entire matching pool for maximum variety.
        """
        if not self.client: return []
        
        try:
            # 1. Get the total count of qualifying questions
            target_type = q_type.lower()
            target_diff = difficulty.lower() if difficulty else None
            
            # Create separate query just for the count
            count_query = self.client.table("questions").select("*", count="exact").eq("type", target_type)
            if target_diff and target_diff != 'all':
                count_query = count_query.eq("difficulty", target_diff)
            
            count_res = self._safe_execute(count_query.limit(1))
            total_count = count_res.count if count_res else 0
            
            if total_count == 0:
                print(f"Warning: No match found for Type={q_type}, Difficulty={difficulty}")
                return []

            # 2. Calculate a random offset
            import random
            safe_range = max(0, total_count - limit)
            random_offset = random.randint(0, safe_range)
            
            # 3. Fetch questions with the random offset (Fresh query builder instance)
            fetch_query = self.client.table("questions").select("*").eq("type", target_type)
            if target_diff and target_diff != 'all':
                fetch_query = fetch_query.eq("difficulty", target_diff)
            
            res = self._safe_execute(fetch_query.range(random_offset, random_offset + limit - 1))
            
            if res and res.data:
                questions = res.data
                random.shuffle(questions)
                return questions
            
            return []
        except Exception as e:
            print(f"SUPABASE RANDOM FETCH ERROR: {e}")
            return []

    def batch_insert_questions(self, questions_list):
        """
        Batch inserts a list of questions into the 'questions' table.
        """
        if not self.client: return None
        try:
            # Chunking to avoid large request payload issues
            chunk_size = 50
            results = []
            for i in range(0, len(questions_list), chunk_size):
                chunk = questions_list[i : i + chunk_size]
                res = self._safe_execute(self.client.table("questions").insert(chunk))
                if res and res.data:
                    results.extend(res.data)
            return results
        except Exception as e:
            print(f"SUPABASE BATCH INSERT ERROR: {e}")
            return None

    def get_user_profile(self, user_id, email=None):
        """
        Retrieves user profile data. If missing, attempts lazy initialization.
        """
        if not self.client: return None
        res = self._safe_execute(self.client.table("users").select("*").eq("id", user_id).limit(1))
        
        if res and res.data:
            return res.data[0]
        
        # LAZY INIT: Create record if missing (happens if signup RLS rejected row)
        if email:
            print(f"LAZY SYNC: Initializing profile record for {user_id}")
            self.create_user_profile(user_id, email)
            # Re-fetch after creation
            res = self._safe_execute(self.client.table("users").select("*").eq("id", user_id).limit(1))
            return res.data[0] if res and res.data else None
            
        return None

    def create_user_profile(self, user_id, email):
        """
        Explicitly creates a record in the custom 'users' table.
        """
        if not self.client: return None
        user_data = {
            "id": user_id, 
            "email": email,
            "full_name": email.split('@')[0].capitalize()
        }
        return self._safe_execute(self.client.table("users").upsert(user_data))

    def update_user_profile(self, user_id, updates):
        """
        Updates user profile data in the custom 'users' table.
        """
        if not self.client: return None
        return self._safe_execute(self.client.table("users").update(updates).eq("id", user_id))

    def upload_avatar(self, user_id, file_bytes, filename):
        """
        Uploads an avatar to storage.
        """
        if not self.client: return None
        path = f"avatars/{user_id}_{filename}"
        self.client.storage.from_("avatars").upload(
            path=path,
            file=file_bytes,
            file_options={"upsert": "true", "content-type": "image/jpeg"}
        )
        url_res = self.client.storage.from_("avatars").get_public_url(path)
        return url_res if url_res else None
