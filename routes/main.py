from flask import Blueprint, render_template, session, redirect, url_for
from extensions import supabase
from auth import get_current_user_id

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Landing page.
    """
    return render_template('index.html', user=True)


@main_bp.route('/results')
def results():
    """
    Show final results and save to history.
    """

    # 🔐 Get authenticated user
    user_id = get_current_user_id()

    if not user_id:
        return {"error": "Unauthorized. Please login."}, 401

    # ---------------- SCORE CALCULATION ---------------- #
    score = session.get('total_score', 0)
    count = session.get('question_count', 0)

    if count > 0:
        if 'aptitude_category' in session:
            avg_score = (score / count) * 100
        else:
            avg_score = (score / count) * 10
    else:
        avg_score = 0

    display_score = round(avg_score, 1)

    # ---------------- SESSION DATA ---------------- #
    is_aptitude = 'aptitude_category' in session

    if is_aptitude:
        from routes.aptitude import get_apti_feedback
        session_id = session.get('apti_session_id')
        feedbacks = get_apti_feedback(session_id) if session_id else []
    else:
        feedbacks = session.get('feedbacks', [])

    session_data = {
        "user_id": user_id,  # 🔥 IMPORTANT
        "type": "aptitude" if is_aptitude else "interview",
        "category": session.get('aptitude_category', session.get('role')),
        "difficulty": session.get('difficulty', 'normal'),
        "score": display_score
    }

    # ---------------- SAVE TO DATABASE ---------------- #
    try:
        supabase.save_session_result(user_id, session_data, feedbacks)
    except Exception as e:
        print("Error saving session:", e)

    # ---------------- FETCH DATA FOR UI ---------------- #
    role = session.get('role', session.get('aptitude_category'))
    history = session.get('history', [])
    v_count = session.get('violation_count', 0)
    terminated = session.get('is_terminated', False)

    # ---------------- CLEAR SESSION ---------------- #
    keys_to_clear = [
        'role', 'aptitude_category', 'difficulty', 'question_count',
        'history', 'feedbacks', 'current_question', 'current_aptitude',
        'total_score', 'violation_count', 'is_terminated'
    ]

    for k in keys_to_clear:
        session.pop(k, None)

    # ---------------- RENDER ---------------- #
    return render_template(
        'results.html',
        role=role,
        avg_score=display_score,
        history=history,
        feedbacks=feedbacks,
        is_aptitude=is_aptitude,
        violation_count=v_count,
        is_terminated=terminated
    )


@main_bp.route('/about/interview')
def about_interview():
    return render_template('about_details.html',
                           title="AI Interview Practice",
                           icon="fa-solid fa-robot",
                           accent_color="#00d4ff",
                           description="Practice your job interviews with our friendly AI. It acts just like a real interviewer, asking you questions and listening to your answers. After the practice, it gives you simple tips on how to speak better and improve your technical answers.",
                           sub_features=[
                               {"icon": "fa-solid fa-brain", "title": "Smart Questions",
                                   "desc": "The AI asks harder or easier questions depending on how well you answer, just like a real interview."},
                               {"icon": "fa-solid fa-comments", "title": "Helpful Tips",
                                   "desc": "Get instant feedback on what you said well and what you can say better next time."},
                               {"icon": "fa-solid fa-chart-simple", "title": "Track Progress",
                                   "desc": "See a simple score that shows your strengths and what you need to work on."}
                           ],
                           cta_link="/interview_start",
                           action_label="Practice")


@main_bp.route('/about/resume')
def about_resume():
    return render_template('about_details.html',
                           title="Resume Builder & Checker",
                           icon="fa-solid fa-file-contract",
                           accent_color="#8b5cf6",
                           description="Make your resume perfect for top companies. You can build a new resume from scratch using our easy tools or upload your current one to see how well it scores. Our AI helps you find missing words and skills that companies look for.",
                           sub_features=[
                               {"icon": "fa-solid fa-code", "title": "Easy Resume Builder",
                                   "desc": "Create a professional resume in minutes using our simple builder—no coding or design skills needed."},
                               {"icon": "fa-solid fa-bullseye", "title": "Company Score",
                                   "desc": "See if your resume can pass the automatic filters that big companies use to scan applications."},
                               {"icon": "fa-solid fa-key", "title": "Better Keywords",
                                   "desc": "We tell you exactly which skills or words are missing from your resume to help you get noticed."},
                               {"icon": "fa-solid fa-wand-magic-sparkles", "title": "Fast Feedback",
                                   "desc": "Get quick advice on how to make your resume look and sound more professional."}
                           ],
                           cta_link="/resume",
                           action_label="Resume Tools")


@main_bp.route('/about/aptitude')
def about_aptitude():
    return render_template('about_details.html',
                           title="Aptitude Training",
                           icon="fa-solid fa-brain",
                           accent_color="#f43f5e",
                           description="Get ready for placement tests by practicing Math, Logic, and English. We have hundreds of questions ranging from very easy to hard. Practice as much as you want to improve your speed and accuracy.",
                           sub_features=[
                               {"icon": "fa-solid fa-calculator", "title": "Math Skills",
                                   "desc": "Practice numbers, percentages, and calculations to solve math problems faster."},
                               {"icon": "fa-solid fa-puzzle-piece", "title": "Logic & Puzzles",
                                   "desc": "Solve tricky puzzles and patterns to sharpen your brain and thinking skills."},
                               {"icon": "fa-solid fa-language", "title": "English Help",
                                   "desc": "Improve your grammar and reading skills to pass the verbal section of any test."}
                           ],
                           cta_link="/aptitude",
                           action_label="Training")


@main_bp.route('/contact')
def contact():
    """
    Dedicated Contact Us page.
    """
    return render_template('contact.html')