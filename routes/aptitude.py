from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import ai
from utils import init_practice_session

aptitude_bp = Blueprint('aptitude', __name__)

@aptitude_bp.route('/aptitude')
def aptitude_select():
    """
    Aptitude category and difficulty selection.
    """
    return render_template('aptitude.html')

@aptitude_bp.route('/start_aptitude', methods=['POST'])
def start_aptitude():
    """
    Initialize aptitude session.
    """
    category = request.form.get('category')
    difficulty = request.form.get('difficulty', 'Medium')
    
    if not category:
        return redirect(url_for('aptitude.aptitude_select'))
    
    init_practice_session(category, is_aptitude=True)
    session['difficulty'] = difficulty
    session['last_question_answered'] = True
    
    return redirect(url_for('aptitude.aptitude_test'))

@aptitude_bp.route('/aptitude_test')
def aptitude_test():
    """
    The aptitude test page.
    """
    if 'aptitude_category' not in session:
        return redirect(url_for('aptitude.aptitude_select'))
    return render_template('aptitude_test.html', 
                           category=session['aptitude_category'],
                           difficulty=session['difficulty'])

@aptitude_bp.route('/api/next_aptitude', methods=['GET'])
def get_next_aptitude():
    """
    API to get next MCQ question.
    """
    if 'aptitude_category' not in session:
        return jsonify({"error": "No session active"}), 400
    
    if session.get('question_count', 0) >= 10:
        return jsonify({"complete": True})
    
    question_data = ai.generate_aptitude_question(
        session['aptitude_category'],
        session['difficulty'],
        session.get('session_seed', 0)
    )
    session['current_aptitude'] = question_data
    session['question_count'] += 1
    session['history'].append(question_data.get('question', ''))
    
    return jsonify({
        "question": question_data.get('question'),
        "options": question_data.get('options'),
        "count": session['question_count'],
        "complete": False
    })

@aptitude_bp.route('/api/check_aptitude', methods=['POST'])
def check_aptitude():
    """
    API to check aptitude answer.
    """
    data = request.json
    user_answer = data.get('answer', '')
    correct_data = session.get('current_aptitude', {})
    
    correct_answer = correct_data.get('correct', 'A')
    is_correct = user_answer == correct_answer
    
    session_feedbacks = session.get('feedbacks', [])
    session_feedbacks.append({
        "question": correct_data.get('question'),
        "score": 10 if is_correct else 0,
        "weakness": "Calculation Error" if not is_correct else ""
    })
    session['feedbacks'] = session_feedbacks

    if is_correct:
        session['total_score'] += 1
    
    return jsonify({
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": correct_data.get('explanation'),
        "next": session.get('question_count', 0) < 10
    })
