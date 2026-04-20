import io
import os
import json
import uuid
import urllib.request
import urllib.parse
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, make_response
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

@resume_bp.route('/builder')
def resume_builder():
    """
    Advanced Resume Builder Interface (Split-screen editor).
    """
    return render_template('resume_builder.html')

@resume_bp.route('/api/resume/compile', methods=['POST'])
def compile_latex():
    """
    Compiles LaTeX to PDF using a free online LaTeX compiler API.
    Returns the compiled PDF or an error.
    """
    data = request.json
    if not data or 'latex' not in data:
        return jsonify({"error": "No LaTeX code provided"}), 400
        
    latex_code = data['latex']
    
    try:
        # Use texlive.net for compilation
        boundary = uuid.uuid4().hex
        payload = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="filecontents[]"; filename="resume.tex"\r\n\r\n'
            f"{latex_code}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="filename[]"\r\n\r\n'
            f"resume.tex\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="engine"\r\n\r\n'
            f"pdflatex\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="return"\r\n\r\n'
            f"pdf\r\n"
            f"--{boundary}--\r\n"
        ).encode('utf-8')
        
        req = urllib.request.Request('https://texlive.net/cgi-bin/latexcgi', data=payload, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        with urllib.request.urlopen(req, timeout=25) as response:
            pdf_data = response.read()
            
            # texlive.net returns PDF directly if return=pdf is set.
            flask_resp = make_response(pdf_data)
            flask_resp.headers['Content-Type'] = 'application/pdf'
            flask_resp.headers['Content-Disposition'] = 'inline; filename=resume.pdf'
            return flask_resp
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"LaTeX Compilation Error: {error_msg}")
        return jsonify({"error": "Failed to compile LaTeX. Template might contain errors.", "details": error_msg}), 400
    except Exception as e:
        print(f"Compilation Server Error: {e}")
        return jsonify({"error": f"Internal server error or external service unavailable: {str(e)}"}), 500

@resume_bp.route('/api/resume/analyze_latex', methods=['POST'])
def analyze_latex():
    """
    Analyzes the raw LaTeX text using AI for ATS matching.
    """
    data = request.json
    if not data or 'latex' not in data:
        return jsonify({"error": "No LaTeX code provided"}), 400
        
    latex_code = data['latex']
    jd = data.get('jd', '')
    
    try:
        user_id = get_current_user_id() or DEFAULT_USER_ID
        
        # Analyze using existing AI handler (passing raw LaTeX can work, 
        # but the AI handler might need to instruction to parse it. 
        # We'll pass it directly as it's very readable for LLMs)
        analysis = ai.analyze_resume(latex_code, jd if jd else None)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500

        # Persist analysis
        save_analysis(user_id, analysis)
        session['analysis_ready_id'] = user_id
        session.modified = True

        return jsonify({"success": True})
    except Exception as e:
        print(f"Server Error in analyze_latex: {e}")
        return jsonify({"error": "Internal server error analyzing LaTeX."}), 500
