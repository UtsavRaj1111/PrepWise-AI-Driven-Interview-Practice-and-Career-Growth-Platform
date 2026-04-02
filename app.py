from flask import Flask
from extensions import ai, supabase

# Blueprint Imports
from routes.main import main_bp
from routes.interview import interview_bp
from routes.aptitude import aptitude_bp
from routes.resume import resume_bp
from routes.mentor import mentor_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.secret_key = 'architect-ai-prepwise-secret-2026-xk9'

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(aptitude_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(mentor_bp)
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':
    # Initialize Handlers (already done in extensions.py via import)
    print("🚀 PrepWise Logic Engine: INITIALIZED")
    app.run(debug=True)
