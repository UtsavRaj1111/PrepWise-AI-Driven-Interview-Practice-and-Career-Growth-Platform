from extensions import supabase_client, supabase
from flask import session

# ------------------ SIGN UP ------------------ #
def register_user(email, password):
    try:
        response = supabase_client.auth.sign_up({
            "email": email,
            "password": password
        })

        if response and response.user:
            return response, None

        return None, "Registration failed."

    except Exception as e:
        err_msg = str(e).lower()
        if "user already registered" in err_msg:
            return None, "This signal is already in the matrix. Try logging in!"
        return None, str(e)


# ------------------ LOGIN ------------------ #
def login_user(email, password):
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response and response.session:
            # 🔥 store token in Flask session
            session['access_token'] = response.session.access_token

            return response.session, None

        return None, "Invalid credentials."

    except Exception as e:
        err_msg = str(e).lower()
        if "invalid" in err_msg or "credentials" in err_msg:
            return None, "Identify sequence failed. Incorrect access cipher or unauthorized email."
        elif "connection" in err_msg:
            return None, "Satellite link unstable. Please check your network connection."
        return None, str(e)


# ------------------ GET USER ------------------ #
def get_current_user_id():
    try:
        token = session.get('access_token')

        if not token:
            return None

        user_res = supabase_client.auth.get_user(token)

        if user_res and user_res.user:
            return user_res.user.id

        return None

    except Exception as e:
        print("Auth Error:", e)
        return None


# ------------------ AUTH CHECK ------------------ #
def is_authenticated():
    return get_current_user_id() is not None