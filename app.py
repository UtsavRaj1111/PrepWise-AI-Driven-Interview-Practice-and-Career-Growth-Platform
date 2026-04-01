from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from ai_handler import AIHandler
from supabase_handler import SupabaseHandler
import os
import io
import pdfplumber

app = Flask(__name__)
app.secret_key = 'architect-ai-prepwise-secret-2026-xk9'

ai = AIHandler()
supabase = SupabaseHandler()

# Default User ID for single-user mode (No Auth)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"

@app.route('/')
def index():
    """
    Landing page with selection between Interview and Aptitude.
    """
    return render_template('index.html', user=True) # Always active

@app.route('/interview_start')
def interview_start():
    """
    Interview role selection page.
    """
    return render_template('interview_select.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """
    Initialize interview session for a specific role.
    """
    role = request.form.get('role')
    if not role:
        return redirect(url_for('interview_start'))
    
    import random
    session['role'] = role
    session['difficulty'] = "Intermediate"
    session['sim_mode'] = request.form.get('sim_mode', 'practice')
    session['total_rounds'] = int(request.form.get('rounds', 1))
    session['current_round'] = 1
    session['question_count'] = 0
    session['history'] = []
    session['feedbacks'] = []
    session['current_question'] = ""
    session['last_question_answered'] = True # Ready for first question
    session['total_score'] = 0
    session['session_seed'] = random.randint(1000, 9999)
    
    return redirect(url_for('interview'))

@app.route('/interview')
def interview():
    """
    The main interview page.
    """
    if 'role' not in session:
        return redirect(url_for('index'))
    return render_template('interview.html', role=session['role'])

@app.route('/api/next_question', methods=['GET'])
def get_next_question():
    """
    Generates and returns the next question. Handles multi-round sessions.
    """
    if 'role' not in session:
        return jsonify({"error": "No session active"}), 400
    
    total_rounds = session.get('total_rounds', 1)
    current_round = session.get('current_round', 1)
    
    # Idempotency check: If current question exists and wasn't answered, return it instead of skipping
    if not session.get('last_question_answered', True) and session.get('current_question'):
        return jsonify({
            "question": session['current_question'],
            "count": session['question_count'],
            "round": session.get('current_round', 1),
            "total_rounds": session.get('total_rounds', 1),
            "difficulty": session.get('difficulty', 'Intermediate'),
            "sim_mode": session.get('sim_mode', 'practice'),
            "complete": False
        })

    if session['question_count'] >= 10:
        # Check if more rounds remain
        if current_round < total_rounds:
            import random
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
        "complete": False
    })

@app.route('/api/evaluate_answer', methods=['POST'])
def evaluate():
    """
    Evaluates the submitted answer and triggers the next step.
    """
    data = request.json
    answer = data.get('answer', '')
    question = session.get('current_question', '')
    role = session.get('role', '')
    
    evaluation = ai.evaluate_answer(question, answer, role)
    
    # Store feedback for Supabase persistence
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
        
        # Adaptive Difficulty Logic
        current_diff = session.get('difficulty', 'Intermediate')
        if score >= 8:
            if current_diff == "Junior": session['difficulty'] = "Intermediate"
            elif current_diff == "Intermediate": session['difficulty'] = "Senior"
        elif score <= 4:
            if current_diff == "Senior": session['difficulty'] = "Intermediate"
            elif current_diff == "Intermediate": session['difficulty'] = "Junior"
    
    return jsonify({
        "evaluation": evaluation,
        "next": session['question_count'] < 10
    })

@app.route('/results')
def results():
    """
    Show final results and ensure they save to history.
    """
    user_id = DEFAULT_USER_ID
    
    score = session.get('total_score', 0)
    count = session.get('question_count', 0)
    avg_score = (score / count * 10) if (not 'aptitude_category' in session and count > 0) else (score / count * 100 if count > 0 else 0)
    
    # Format avg_score for display (0-100%)
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
    
    # Selective clear
    keys_to_clear = ['role', 'aptitude_category', 'difficulty', 'question_count', 'history', 'feedbacks', 'current_question', 'current_aptitude', 'total_score']
    for k in keys_to_clear: session.pop(k, None)

    return render_template('results.html', 
                           role=role, 
                           avg_score=display_score,
                           history=history,
                           feedbacks=feedbacks,
                           is_aptitude=is_aptitude)

# --- Resume Analyzer Logic ---

def extract_text_from_pdf(file_stream):
    try:
        file_stream.seek(0)
        with pdfplumber.open(file_stream) as pdf:
            text = ""
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
        return ""

@app.route('/resume')
def resume_analyzer():
    return render_template('resume_analyzer.html')

@app.route('/api/upload_resume', methods=['POST'])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['resume']
        jd = request.form.get('jd', '')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        filename = file.filename.lower()
        if not filename.endswith('.pdf'):
            return jsonify({"error": "Strictly PDF only. Please upload your resume in PDF format."}), 400
        
        file_stream = io.BytesIO(file.read())
        text = extract_text_from_pdf(file_stream)

        if not text.strip():
            return jsonify({"error": "Could not extract text from the PDF. Ensure it's not scanned or password protected."}), 400

        # Flush old cached results so new upload is always fresh
        session.pop('resume_analysis', None)
        session.pop('resume_questions', None)

        analysis = ai.analyze_resume(text, jd if jd else None)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500

        # Force Flask to re-serialize the session cookie (not just mutate)
        session['resume_analysis'] = dict(analysis)
        session['resume_questions'] = list(analysis.get('questions', []))
        session.modified = True

        return jsonify({"success": True})
    except Exception as e:
        print(f"Server Error in upload_resume: {e}")
        return jsonify({"error": "Internal server error. Please try a different PDF."}), 500

@app.route('/resume_results')
def resume_results():
    analysis = session.get('resume_analysis')
    if not analysis:
        return redirect(url_for('resume_analyzer'))
    return render_template('resume_results.html', analysis=analysis)

# --- AI Mentor Chatbot (Multi-Thread) ---

import uuid
from datetime import datetime

@app.route('/mentor')
def mentor_page():
    """
    Mentor page with sidebar thread management.
    """
    if 'chat_threads' not in session:
        session['chat_threads'] = {}
    
    # Identify the active thread
    thread_id = request.args.get('thread_id')
    
    if not thread_id or thread_id not in session['chat_threads']:
        # Start a new default thread if none active
        thread_id = str(uuid.uuid4())
        session['chat_threads'][thread_id] = {
            "id": thread_id,
            "title": "New Communication Node",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "history": [
                {"role": "assistant", "content": "Hello! I'm your PrepWise Career Mentor. How can I help you today?"}
            ]
        }
        session.modified = True
    
    active_thread = session['chat_threads'][thread_id]
    return render_template('mentor.html', 
                           chat_history=active_thread['history'],
                           active_thread_id=thread_id,
                           threads=session['chat_threads'].values())

@app.route('/api/chat/new', methods=['POST'])
def new_chat_thread():
    thread_id = str(uuid.uuid4())
    if 'chat_threads' not in session:
        session['chat_threads'] = {}
    
    session['chat_threads'][thread_id] = {
        "id": thread_id,
        "title": "New Communication Node",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "history": [
            {"role": "assistant", "content": "Hello! I'm your PrepWise Career Mentor. How can I help you today?"}
        ]
    }
    session.modified = True
    return jsonify({"thread_id": thread_id})

@app.route('/api/chat', methods=['POST'])
def mentor_chat():
    try:
        user_message = request.form.get('message', '').strip()
        uploaded_file = request.files.get('file')
        thread_id = request.form.get('thread_id')
        
        if 'chat_threads' not in session or thread_id not in session['chat_threads']:
             return jsonify({"error": "Invalid thread session"}), 400

        thread = session['chat_threads'][thread_id]
        
        file_context = ""
        if uploaded_file:
            filename = uploaded_file.filename.lower()
            if filename.endswith('.pdf'):
                file_stream = io.BytesIO(uploaded_file.read())
                file_context = extract_text_from_pdf(file_stream)
            elif any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                file_context = f"[Vision Context: The user uploaded an image named {uploaded_file.filename}. Note: Image vision is currently in sandbox mode.]"
        
        if not user_message and not file_context:
            return jsonify({"error": "Empty message"}), 400
        
        # Use AI-determined or first-message-based title if NOT manually edited
        if not thread.get('title_edited') and len(thread['history']) == 1 and user_message:
            thread['title'] = user_message[:40] + ("..." if len(user_message) > 40 else "")
        
        display_message = user_message
        if uploaded_file:
            display_message = f"📎 [{uploaded_file.filename}] {user_message}"
        
        thread['history'].append({"role": "user", "content": display_message})
        
        # Get AI response with context
        ai_response = ai.get_mentor_response(user_message, thread['history'], file_context)
        
        thread['history'].append({"role": "assistant", "content": ai_response})
        session['chat_threads'][thread_id] = thread
        session.modified = True
        
        return jsonify({
            "response": ai_response,
            "thread_id": thread_id,
            "title": thread['title']
        })
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    thread_id = request.json.get('thread_id')
    if 'chat_threads' in session and thread_id in session['chat_threads']:
        session['chat_threads'][thread_id]['history'] = [
            {"role": "assistant", "content": "Hello! I'm your PrepWise Career Mentor. How can I help you today?"}
        ]
        session.modified = True
    return jsonify({"success": True})

@app.route('/api/chat/delete', methods=['POST'])
def delete_chat_thread():
    thread_id = request.json.get('thread_id')
    if 'chat_threads' in session and thread_id in session['chat_threads']:
        session['chat_threads'].pop(thread_id)
        session.modified = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Thread not found"}), 404

@app.route('/api/chat/rename', methods=['POST'])
def rename_chat_thread():
    thread_id = request.json.get('thread_id')
    new_title = request.json.get('new_title', '').strip()
    if not new_title:
        return jsonify({"success": False, "error": "Empty title"}), 400
    
    if 'chat_threads' in session and thread_id in session['chat_threads']:
        session['chat_threads'][thread_id]['title'] = new_title
        session['chat_threads'][thread_id]['title_edited'] = True
        session.modified = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Thread not found"}), 404

# --- Dashboard & Stats ---

@app.route('/dashboard')
def dashboard():
    user_id = DEFAULT_USER_ID
    data = supabase.get_dashboard_data(user_id)
    raw_sessions = data.get('sessions', [])
    
    # Calculate stats
    interview_scores = [s['score'] for s in raw_sessions if s['type'] == 'Interview']
    aptitude_scores = [s['score'] for s in raw_sessions if s['type'] == 'Aptitude']
    
    stats = {
        "avg_interview": round(sum(interview_scores) / len(interview_scores), 1) if interview_scores else 0,
        "apt_accuracy": round(sum(aptitude_scores) / len(aptitude_scores), 1) if aptitude_scores else 0,
        "total_sessions": len(raw_sessions)
    }
    
    # 7-Day Logic for the Chart
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    logs_7_days = [s for s in raw_sessions if datetime.fromisoformat(s['created_at'].replace('Z', '')) > seven_days_ago]

    return render_template('dashboard.html', 
                           stats=stats,
                           logs=logs_7_days if logs_7_days else raw_sessions[:10]) # Fallback to last 10 if none in 7 days

# --- Aptitude Routes ---

@app.route('/aptitude')
def aptitude_select():
    """
    Aptitude category and difficulty selection.
    """
    return render_template('aptitude.html')

@app.route('/start_aptitude', methods=['POST'])
def start_aptitude():
    """
    Initialize aptitude session.
    """
    import random
    category = request.form.get('category')
    difficulty = request.form.get('difficulty', 'Medium')
    
    if not category:
        return redirect(url_for('aptitude_select'))
    
    session['aptitude_category'] = category
    session['difficulty'] = difficulty
    session['question_count'] = 0
    session['history'] = []
    session['feedbacks'] = []
    session['total_score'] = 0
    session['session_seed'] = random.randint(1000, 9999)  # Force fresh unique questions
    
    return redirect(url_for('aptitude_test'))

@app.route('/aptitude_test')
def aptitude_test():
    """
    The aptitude test page.
    """
    if 'aptitude_category' not in session:
        return redirect(url_for('aptitude_select'))
    return render_template('aptitude_test.html', 
                           category=session['aptitude_category'],
                           difficulty=session['difficulty'])

@app.route('/api/next_aptitude', methods=['GET'])
def get_next_aptitude():
    """
    API to get next MCQ question.
    """
    if 'aptitude_category' not in session:
        return jsonify({"error": "No session active"}), 400
    
    if session['question_count'] >= 10:
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

@app.route('/api/check_aptitude', methods=['POST'])
def check_aptitude():
    """
    API to check aptitude answer.
    """
    data = request.json
    user_answer = data.get('answer', '') # e.g. "B"
    correct_data = session.get('current_aptitude', {})
    
    correct_answer = correct_data.get('correct', 'A')
    is_correct = user_answer == correct_answer
    
    # Store feedback for aptitude
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
        "next": session['question_count'] < 10
    })

if __name__ == '__main__':
    app.run(debug=True)
