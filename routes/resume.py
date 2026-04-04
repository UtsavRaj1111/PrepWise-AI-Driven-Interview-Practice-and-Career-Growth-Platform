import io
import os
import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import supabase
from ai_handler import ai
from utils import extract_text_from_pdf, DEFAULT_USER_ID
from auth import get_current_user_id

resume_bp = Blueprint('resume', __name__)

# Persistent analysis storage to bypass 4KB cookie limit and survive server reloads
RESUME_CACHE_DIR = os.path.join(os.getcwd(), 'tmp', 'resume_cache')
os.makedirs(RESUME_CACHE_DIR, exist_ok=True)

def save_analysis(user_id, data):
    cache_path = os.path.join(RESUME_CACHE_DIR, f"{user_id}.json")
    with open(cache_path, 'w') as f:
        json.dump(data, f)

def load_analysis(user_id):
    cache_path = os.path.join(RESUME_CACHE_DIR, f"{user_id}.json")
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

@resume_bp.route('/resume')
def resume_analyzer():
    """
    Resume analyzer selection.
    """
    return render_template('resume_analyzer.html')

@resume_bp.route('/api/upload_resume', methods=['POST'])
def upload_resume():
    """
    API to upload and analyze resume.
    """
    try:
        user_id = get_current_user_id() or DEFAULT_USER_ID
        
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

        # Run AI Analysis
        analysis = ai.analyze_resume(text, jd if jd else None)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500

        # Persist analysis result to file cache
        save_analysis(user_id, analysis)
        
        # Keep session light - only store a ready flag
        session['analysis_ready_id'] = user_id
        session.modified = True

        return jsonify({"success": True})
    except Exception as e:
        print(f"Server Error in upload_resume: {e}")
        return jsonify({"error": "Internal server error. Please try a different PDF."}), 500

@resume_bp.route('/resume_results')
def resume_results():
    """
    Show resonance results.
    """
    user_id = session.get('analysis_ready_id')
    if not user_id:
        # Fallback to current user if session marker lost but file exists
        user_id = get_current_user_id() or DEFAULT_USER_ID
    
    analysis = load_analysis(user_id)
    if not analysis:
        print(f"CACHE MISS: No analysis found for user {user_id}")
        return redirect(url_for('resume.resume_analyzer'))
        
    return render_template('resume_results.html', analysis=analysis)
