let timerInterval;
let timeLeft = 60;
let currentQuestionCount = 1;
let isRecording = false;
let recognition;

// Initialize components
document.addEventListener('DOMContentLoaded', () => {
    loadFirstQuestion();
    setupVoiceRecognition();
    
    document.getElementById('submit-btn').addEventListener('click', submitAnswer);
    document.getElementById('mic-btn').addEventListener('click', toggleMic);
    document.getElementById('next-btn').addEventListener('click', () => {
        document.getElementById('feedback-area').style.display = 'none';
        document.getElementById('answer-input').value = '';
        loadFirstQuestion(); // Reuse for next question
    });
});

async function loadFirstQuestion() {
    showLoading(true);
    try {
        const response = await fetch('/api/next_question');
        const data = await response.json();
        
        if (data.complete) {
            showCompletion();
        } else {
            displayQuestion(data.question, data.count);
            startTimer();
        }
    } catch (e) {
        console.error("Error loading question", e);
    } finally {
        showLoading(false);
    }
}

function startTimer() {
    clearInterval(timerInterval);
    timeLeft = 60;
    const timerEl = document.getElementById('timer');
    timerEl.innerText = timeLeft;
    
    timerInterval = setInterval(() => {
        timeLeft--;
        timerEl.innerText = timeLeft;
        
        if (timeLeft <= 10) {
            timerEl.style.color = '#ef4444';
            timerEl.style.borderColor = '#ef4444';
        } else {
            timerEl.style.color = 'var(--primary)';
            timerEl.style.borderColor = 'var(--primary)';
        }
        
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            submitAnswer(); // Auto-submit on timeout
        }
    }, 1000);
}

async function submitAnswer() {
    clearInterval(timerInterval);
    const answer = document.getElementById('answer-input').value;
    const submitBtn = document.getElementById('submit-btn');
    
    submitBtn.disabled = true;
    submitBtn.innerText = "Evaluating...";
    
    try {
        const response = await fetch('/api/evaluate_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: answer })
        });
        const data = await response.json();
        
        showFeedback(data.evaluation);
    } catch (e) {
        console.error("Evaluation error", e);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Answer";
    }
}

function showFeedback(evaluation) {
    document.getElementById('feedback-area').style.display = 'block';
    
    // Updated mapping for new criteria-based feedback
    document.getElementById('feedback-score').innerText = `${evaluation.score}/10`;
    document.getElementById('feedback-strength').innerText = evaluation.strength || "N/A";
    document.getElementById('feedback-weakness').innerText = evaluation.weakness || "N/A";
    document.getElementById('feedback-suggestion').innerText = evaluation.suggestion || "N/A";
    document.getElementById('feedback-sample').innerText = evaluation.sample_answer || "N/A";
    
    // Smooth scroll to feedback
    document.getElementById('feedback-area').scrollIntoView({ behavior: 'smooth' });
}

function showLoading(isLoading) {
    document.getElementById('loading').style.display = isLoading ? 'block' : 'none';
    document.getElementById('interview-container').style.display = isLoading ? 'none' : 'flex';
}

function displayQuestion(question, count) {
    document.getElementById('question-area').innerText = question;
    document.getElementById('progress-text').innerText = `Question ${count} of 10`;
}

function showCompletion() {
    document.getElementById('interview-container').style.display = 'none';
    document.getElementById('completion-area').style.display = 'block';
}

// --- Voice Recognition ---

function setupVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('mic-btn').style.display = 'none';
        console.warn("Speech recognition not supported in this browser.");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        if (finalTranscript) {
            document.getElementById('answer-input').value += finalTranscript + ' ';
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);
        stopRecording();
    };

    recognition.onend = () => {
        if (isRecording) recognition.start(); // Keep recording if still active
    };
}

function toggleMic() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    isRecording = true;
    recognition.start();
    const micBtn = document.getElementById('mic-btn');
    micBtn.classList.add('active');
    micBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Mic';
}

function stopRecording() {
    isRecording = false;
    recognition.stop();
    const micBtn = document.getElementById('mic-btn');
    micBtn.classList.remove('active');
    micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> Voice Input';
}
