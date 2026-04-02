import uuid
import io
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from extensions import ai
from utils import extract_text_from_pdf

mentor_bp = Blueprint('mentor', __name__)

@mentor_bp.route('/mentor')
def mentor_page():
    """
    Mentor page with sidebar thread management.
    """
    if 'chat_threads' not in session:
        session['chat_threads'] = {}
    
    thread_id = request.args.get('thread_id')
    
    if not thread_id or thread_id not in session['chat_threads']:
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

@mentor_bp.route('/api/chat/new', methods=['POST'])
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

@mentor_bp.route('/api/chat', methods=['POST'])
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
        
        if not thread.get('title_edited') and len(thread['history']) == 1 and user_message:
            thread['title'] = user_message[:40] + ("..." if len(user_message) > 40 else "")
        
        display_message = user_message
        if uploaded_file:
            display_message = f"📎 [{uploaded_file.filename}] {user_message}"
        
        thread['history'].append({"role": "user", "content": display_message})
        
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

@mentor_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    thread_id = request.json.get('thread_id')
    if 'chat_threads' in session and thread_id in session['chat_threads']:
        session['chat_threads'][thread_id]['history'] = [
            {"role": "assistant", "content": "Hello! I'm your PrepWise Career Mentor. How can I help you today?"}
        ]
        session.modified = True
    return jsonify({"success": True})

@mentor_bp.route('/api/chat/delete', methods=['POST'])
def delete_chat_thread():
    thread_id = request.json.get('thread_id')
    if 'chat_threads' in session and thread_id in session['chat_threads']:
        session['chat_threads'].pop(thread_id)
        session.modified = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Thread not found"}), 404

@mentor_bp.route('/api/chat/rename', methods=['POST'])
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
