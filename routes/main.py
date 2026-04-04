from flask import Blueprint, render_template, session, redirect, url_for
from extensions import supabase
from auth import get_current_user_id

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

    # 🔐 Get authenticated user
    user_id = get_current_user_id()

    if not user_id:
        return {"error": "Unauthorized. Please login."}, 401

    # ---------------- SCORE CALCULATION ---------------- #
    score = session.get('total_score', 0)
    count = session.get('question_count', 0)

    if count > 0:
        if 'aptitude_category' in session:
            avg_score = (score / count) * 100
        else:
            avg_score = (score / count) * 10
    else:
        avg_score = 0

    display_score = round(avg_score, 1)

    # ---------------- SESSION DATA ---------------- #
    is_aptitude = 'aptitude_category' in session

    session_data = {
        "user_id": user_id,  # 🔥 IMPORTANT
        "type": "aptitude" if is_aptitude else "interview",
        "category": session.get('aptitude_category', session.get('role')),
        "difficulty": session.get('difficulty', 'normal'),
        "score": display_score
    }

    feedbacks = session.get('feedbacks', [])

    # ---------------- SAVE TO DATABASE ---------------- #
    try:
        supabase.save_session_result(user_id, session_data, feedbacks)
    except Exception as e:
        print("Error saving session:", e)

    # ---------------- FETCH DATA FOR UI ---------------- #
    role = session.get('role', session.get('aptitude_category'))
    history = session.get('history', [])
    v_count = session.get('violation_count', 0)
    terminated = session.get('is_terminated', False)

    # ---------------- CLEAR SESSION ---------------- #
    keys_to_clear = [
        'role', 'aptitude_category', 'difficulty', 'question_count',
        'history', 'feedbacks', 'current_question', 'current_aptitude',
        'total_score', 'violation_count', 'is_terminated'
    ]

    for k in keys_to_clear:
        session.pop(k, None)

    # ---------------- RENDER ---------------- #
    return render_template(
        'results.html',
        role=role,
        avg_score=display_score,
        history=history,
        feedbacks=feedbacks,
        is_aptitude=is_aptitude,
        violation_count=v_count,
        is_terminated=terminated
    )