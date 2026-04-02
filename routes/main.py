from flask import Blueprint, render_template, session
from extensions import supabase
from utils import DEFAULT_USER_ID

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Landing page.
    """
    return render_template('index.html', user=True)

@main_bp.route('/results')
def results():
    """
    Show final results and save to history.
    """
    user_id = DEFAULT_USER_ID
    
    score = session.get('total_score', 0)
    count = session.get('question_count', 0)
    avg_score = (score / count * 10) if (not 'aptitude_category' in session and count > 0) else (score / count * 100 if count > 0 else 0)
    display_score = round(avg_score if not 'aptitude_category' in session else (score/count*100), 1)

    # Save to Supabase
    is_aptitude = 'aptitude_category' in session
    session_data = {
        "type": "Aptitude" if is_aptitude else "Interview",
        "category": session.get('aptitude_category', session.get('role')),
        "difficulty": session.get('difficulty', 'Normal'),
        "score": display_score
    }
    
    feedbacks = session.get('feedbacks', [])
    supabase.save_session_result(user_id, session_data, feedbacks)
    
    role = session.get('role', session.get('aptitude_category'))
    history = session.get('history', [])
    v_count = session.get('violation_count', 0)
    terminated = session.get('is_terminated', False)
    
    # Selective clear
    keys_to_clear = ['role', 'aptitude_category', 'difficulty', 'question_count', 'history', 'feedbacks', 
                     'current_question', 'current_aptitude', 'total_score', 'violation_count', 'is_terminated']
    for k in keys_to_clear: session.pop(k, None)

    return render_template('results.html', 
                           role=role, 
                           avg_score=display_score,
                           history=history,
                           feedbacks=feedbacks,
                           is_aptitude=is_aptitude,
                           violation_count=v_count,
                           is_terminated=terminated)
