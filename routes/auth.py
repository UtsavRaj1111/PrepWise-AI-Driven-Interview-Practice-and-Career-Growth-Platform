from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth import register_user, login_user
from extensions import supabase

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Register with Supabase Auth
        res, error = register_user(email, password)
        
        if error:
            flash(error, 'error')
            return render_template('auth/signup.html')
        
        flash("Signal Linked! Please log in to synchronize your neural profile.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Authenticate
        session_obj, error = login_user(email, password)
        
        if error:
            flash(error, 'error')
            return render_template('auth/login.html')
        
        # 2. Persist Identity to Session (Essential for UI/Header)
        user_id = session_obj.user.id
        session['user_id'] = user_id
        session['email'] = email
        session['user_name'] = email.split('@')[0].capitalize() # Early-access name
        
        # 3. Synchronize Detailed Profile (Lazy Initialization)
        try:
            profile = supabase.get_user_profile(user_id, email=email)
            if profile:
                session['user_name'] = profile.get('full_name', session['user_name'])
                session['avatar_url'] = profile.get('avatar_url')
        except Exception as e:
            print(f"Profile Sync Warning: {e}")

        session.modified = True
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    supabase.sign_out() # Clears Supabase client and Flask session
    return redirect(url_for('main.index'))
