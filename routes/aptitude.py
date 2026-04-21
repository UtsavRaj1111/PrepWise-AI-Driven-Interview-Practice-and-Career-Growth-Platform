import os
import json
import uuid
import random
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import supabase
from ai_handler import ai
from utils import init_practice_session, DEFAULT_USER_ID
from auth import get_current_user_id

aptitude_bp = Blueprint('aptitude', __name__)

# Persistent storage for questions to survive reload and bypass 4KB cookie limit
APTI_CACHE_DIR = os.path.join(os.getcwd(), 'tmp', 'apti_cache')
os.makedirs(APTI_CACHE_DIR, exist_ok=True)

def save_apti_pool(session_id, pool):
    path = os.path.join(APTI_CACHE_DIR, f"{session_id}.json")
    with open(path, 'w') as f:
        json.dump(pool, f)

def get_apti_pool(session_id):
    path = os.path.join(APTI_CACHE_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def save_apti_feedback(session_id, feedbacks):
    path = os.path.join(APTI_CACHE_DIR, f"{session_id}_feedback.json")
    with open(path, 'w') as f:
        json.dump(feedbacks, f)

def get_apti_feedback(session_id):
    path = os.path.join(APTI_CACHE_DIR, f"{session_id}_feedback.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def resolve_answer_letter(question):
    """
    Translates 'answer' field into a single letter (A, B, C, D).
    Handles both letter-based and text-based correct answers.
    """
    ans = question.get('answer') or question.get('correct')
    if not ans:
        return 'A'
        
    ans_str = str(ans).strip()
    
    # CASE 1: Already a letter
    if len(ans_str) == 1 and ans_str.upper() in ['A', 'B', 'C', 'D']:
        return ans_str.upper()
        
    # CASE 2: Full text (e.g. "$112")
    options = question.get('options', [])
    for idx, opt in enumerate(options):
        if str(opt).strip() == ans_str:
            return chr(65 + idx)
            
    # CASE 3: Prefix matching
    for idx, opt in enumerate(options):
        if ans_str.startswith(f"{chr(65 + idx)}."):
            return chr(65 + idx)
            
    return 'A' 

@aptitude_bp.route('/aptitude')
def aptitude_select():
    return render_template('aptitude.html')

@aptitude_bp.route('/start_aptitude', methods=['POST'])
def start_aptitude():
    category = request.form.get('category')
    difficulty = request.form.get('difficulty', 'Medium')
    
    if not category:
        return redirect(url_for('aptitude.aptitude_select'))
    
    init_practice_session(category, is_aptitude=True)
    session['difficulty'] = difficulty
    session['last_question_answered'] = True
    
    user_id = get_current_user_id() or DEFAULT_USER_ID
    apti_session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
    session['apti_session_id'] = apti_session_id

    type_map = {"Quantitative": "aptitude", "Logical": "lr", "Verbal": "va"}
    db_type = type_map.get(category, "aptitude")
    
    questions_pool = supabase.get_random_questions(db_type, difficulty, limit=10)
    
    if questions_pool and len(questions_pool) > 0:
        save_apti_pool(apti_session_id, questions_pool)
        session['use_db'] = True
    else:
        session['use_db'] = False
    
    session.modified = True
    return redirect(url_for('aptitude.aptitude_test'))

@aptitude_bp.route('/aptitude_test')
def aptitude_test():
    if 'aptitude_category' not in session:
        return redirect(url_for('aptitude.aptitude_select'))
    return render_template('aptitude_test.html', 
                           category=session['aptitude_category'],
                           difficulty=session.get('difficulty', 'Medium'))

@aptitude_bp.route('/api/next_aptitude', methods=['GET'])
def get_next_aptitude():
    if 'aptitude_category' not in session:
        return jsonify({"error": "No session active"}), 400
    
    idx = session.get('question_count', 0)
    if idx >= 10:
        return jsonify({"complete": True})

    session_id = session.get('apti_session_id')
    pool = get_apti_pool(session_id) if session_id else None
    
    if not pool or idx >= len(pool):
        question = ai.generate_aptitude_question(
            session['aptitude_category'], 
            session.get('difficulty', 'Medium'),
            session.get('session_seed', 0)
        )
    else:
        question = pool[idx]

    # Resolve Correct Answer Letter (BEFORE shuffling or modifying)
    correct_letter = resolve_answer_letter(question)
    correct_text = ""
    
    options = list(question.get('options', []))
    if len(options) >= 4:
        # Determine the text of the correct answer
        letter_idx = ord(correct_letter) - 65
        if 0 <= letter_idx < len(options):
            correct_text = options[letter_idx]

        import re
        options = [re.sub(r'^[A-D][\.\)]\s+', '', str(opt).strip()) for opt in options]
        correct_text = re.sub(r'^[A-D][\.\)]\s+', '', str(correct_text).strip())

        # SHUFFLE LOGIC
        # We store the text of the correct answer, shuffle the options, 
        # then find the NEW index of that text to update the correct letter.
        random.shuffle(options)
        
        # Update resolved_correct to point to the new index
        for i, opt in enumerate(options):
            if opt == correct_text:
                question['resolved_correct'] = chr(65 + i)
                break
    else:
        question['resolved_correct'] = correct_letter

    session['resolved_correct'] = question.get('resolved_correct', correct_letter)
    session.pop('current_aptitude', None)
    session['last_question_answered'] = False
    session.modified = True
    
    return jsonify({
        "question": question.get('question'),
        "options": options,
        "count": idx + 1,
        "complete": False
    })

@aptitude_bp.route('/api/check_aptitude', methods=['POST'])
def check_aptitude():
    data = request.json
    user_answer = data.get('answer', '')
    
    correct_answer = session.get('resolved_correct', 'A')
    is_correct = (user_answer == correct_answer)
    
    session_id = session.get('apti_session_id')
    session_feedbacks = get_apti_feedback(session_id) if session_id else []

    idx = session.get('question_count', 0)
    pool = get_apti_pool(session_id) if session_id else None
    
    question_text = ""
    explanation = ""
    if pool and idx < len(pool):
        question_text = pool[idx].get('question', '')
        explanation = pool[idx].get('explanation', '')
    
    session_feedbacks.append({
        "question": question_text,
        "score": 10 if is_correct else 0,
        "weakness": "Concept Gap" if not is_correct else "",
        "suggestion": explanation if not is_correct else "Exemplary logic applied."
    })
    
    if session_id:
        save_apti_feedback(session_id, session_feedbacks)

    if is_correct:
        session['total_score'] += 1
        
    current_count = session.get('question_count', 0)
    session['question_count'] = current_count + 1
    session.modified = True
    
    return jsonify({
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "next": session['question_count'] < 10
    })
