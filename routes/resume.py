import io
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import ai
from utils import extract_text_from_pdf

resume_bp = Blueprint('resume', __name__)

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

        session.pop('resume_analysis', None)
        session.pop('resume_questions', None)

        analysis = ai.analyze_resume(text, jd if jd else None)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500

        session['resume_analysis'] = dict(analysis)
        session['resume_questions'] = list(analysis.get('questions', []))
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
    analysis = session.get('resume_analysis')
    if not analysis:
        return redirect(url_for('resume.resume_analyzer'))
    return render_template('resume_results.html', analysis=analysis)
