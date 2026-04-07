import random
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from ai_handler import ai
from utils import init_practice_session

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/interview_start')
def interview_start():
    """
    Interview role selection page.
    """
    return render_template('interview_select.html')

@interview_bp.route('/start_interview', methods=['POST'])
def start_interview():
    """
    Initialize interview session.
    """
    role = request.form.get('role')
    if not role:
        return redirect(url_for('interview.interview_start'))
    
    init_practice_session(role, is_aptitude=False)
    session['sim_mode'] = request.form.get('sim_mode', 'practice')
    session['total_rounds'] = int(request.form.get('rounds', 1))
    session['current_round'] = 1
    session['last_question_answered'] = True
    
    return redirect(url_for('interview.interview'))

@interview_bp.route('/interview')
def interview():
    """
    The main interview page.
    """
    if 'role' not in session:
        return redirect(url_for('main.index'))
    return render_template('interview.html', role=session['role'])

@interview_bp.route('/api/next_question', methods=['GET'])
def get_next_question():
    """
    Generates and returns the next question.
    """
    if 'role' not in session:
        return jsonify({"error": "No session active"}), 400
    
    total_rounds = session.get('total_rounds', 1)
    current_round = session.get('current_round', 1)
    
    if not session.get('last_question_answered', True) and session.get('current_question'):
        return jsonify({
            "question": session['current_question'],
            "count": session['question_count'],
            "round": current_round,
            "total_rounds": total_rounds,
            "difficulty": session.get('difficulty', 'Intermediate'),
            "sim_mode": session.get('sim_mode', 'practice'),
            "complete": False
        })

    if session.get('question_count', 0) >= 10:
        if current_round < total_rounds:
            session['current_round'] = current_round + 1
            session['question_count'] = 0
            session['session_seed'] = random.randint(1000, 9999)
            session['last_question_answered'] = True
        else:
            return jsonify({"complete": True})
    
    question = ai.generate_question(
        session['role'],
        session['history'],
        session.get('difficulty', 'Intermediate'),
        session.get('session_seed', 0)
    )
    session['current_question'] = question
    session['question_count'] += 1
    session['last_question_answered'] = False
    session['history'].append(question)
    
    return jsonify({
        "question": question,
        "count": session['question_count'],
        "round": session.get('current_round', 1),
        "total_rounds": session.get('total_rounds', 1),
        "difficulty": session.get('difficulty', 'Intermediate'),
        "sim_mode": session.get('sim_mode', 'practice'),
        "complete": False,
        "is_terminated": session.get('is_terminated', False)
    })

@interview_bp.route('/api/evaluate_answer', methods=['POST'])
def evaluate():
    """
    Evaluates the submitted answer.
    """
    data = request.json
    answer = data.get('answer', '')
    question = session.get('current_question', '')
    role = session.get('role', '')
    
    evaluation = ai.evaluate_answer(question, answer, role)
    
    session_feedbacks = session.get('feedbacks', [])
    session_feedbacks.append({
        "question": question,
        "score": evaluation.get('score', 0),
        "strength": evaluation.get('strength', ''),
        "weakness": evaluation.get('weakness', ''),
        "suggestion": evaluation.get('suggestion', '')
    })
    session['feedbacks'] = session_feedbacks
    session['last_question_answered'] = True

    if 'score' in evaluation:
        score = evaluation['score']
        session['total_score'] += score
        current_diff = session.get('difficulty', 'Intermediate')
        if score >= 8:
            if current_diff == "Junior": session['difficulty'] = "Intermediate"
            elif current_diff == "Intermediate": session['difficulty'] = "Senior"
        elif score <= 4:
            if current_diff == "Senior": session['difficulty'] = "Intermediate"
            elif current_diff == "Intermediate": session['difficulty'] = "Junior"
    
    return jsonify({
        "evaluation": evaluation,
        "next": session['question_count'] < 10,
        "is_terminated": session.get('is_terminated', False)
    })

@interview_bp.route('/api/report_violation', methods=['POST'])
def report_violation():
    """
    Increments violation count.
    """
    if 'violation_count' not in session:
        session['violation_count'] = 0
    
    session['violation_count'] += 1
    if session['violation_count'] >= 3:
        session['is_terminated'] = True
    
    return jsonify({
        "count": session['violation_count'],
        "is_terminated": session.get('is_terminated', False),
        "warning": "VIOLATION DETECTED: This incident has been logged."
    })
