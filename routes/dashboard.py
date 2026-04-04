from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, redirect, url_for
from auth import get_current_user_id
from extensions import supabase

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    """
    User dashboard with analytics fetching from the authenticated session.
    """
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for('auth.login'))
        
    data = supabase.get_dashboard_data(user_id)
    raw_sessions = data.get('sessions', [])
    
    interview_scores = [s['score'] for s in raw_sessions if s['type'] == 'Interview']
    aptitude_scores = [s['score'] for s in raw_sessions if s['type'] == 'Aptitude']
    
    stats = {
        "avg_interview": round(sum(interview_scores) / len(interview_scores), 1) if interview_scores else 0,
        "apt_accuracy": round(sum(aptitude_scores) / len(aptitude_scores), 1) if aptitude_scores else 0,
        "total_sessions": len(raw_sessions)
    }
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    logs_7_days = [s for s in raw_sessions if datetime.fromisoformat(s['created_at'].replace('Z', '')) > seven_days_ago]

    return render_template('dashboard.html', 
                           stats=stats,
                           logs=logs_7_days if logs_7_days else raw_sessions[:10])
