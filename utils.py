import random
import io
import pdfplumber
from flask import session

# Default User ID for single-user mode (No Auth)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"

def init_practice_session(category, is_aptitude=False):
    """
    Common session initializer for Interview and Aptitude.
    Ensures a fresh state for every test.
    """
    keys_to_clear = ['role', 'aptitude_category', 'difficulty', 'question_count', 'history', 'feedbacks', 
                     'current_question', 'current_aptitude', 'total_score', 'violation_count', 'is_terminated',
                     'total_rounds', 'current_round', 'session_seed', 'last_question_answered']
    for k in keys_to_clear: session.pop(k, None)
    
    if is_aptitude:
        session['aptitude_category'] = category
    else:
        session['role'] = category
        
    session['difficulty'] = "Intermediate"
    session['question_count'] = 0
    session['history'] = []
    session['feedbacks'] = []
    session['total_score'] = 0
    session['session_seed'] = random.randint(1000, 9999)
    session['violation_count'] = 0
    session['is_terminated'] = False
    session.modified = True

def extract_text_from_pdf(file_stream):
    """
    Utility to extract text content from PDF bytes.
    """
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
