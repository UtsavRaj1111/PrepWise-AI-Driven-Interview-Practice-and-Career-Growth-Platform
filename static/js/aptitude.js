let timerInterval;
let timeLeft = 60;
let currentQuestionCount = 1;
let selectedOption = null;

// Initialize components
document.addEventListener('DOMContentLoaded', () => {
    loadNextQuestion();
    
    document.getElementById('submit-btn').addEventListener('click', submitAnswer);
    document.getElementById('next-btn').addEventListener('click', () => {
        document.getElementById('explanation-area').style.display = 'none';
        selectedOption = null;
        loadNextQuestion();
    });
});

async function loadNextQuestion() {
    showLoading(true);
    try {
        const response = await fetch('/api/next_aptitude');
        const data = await response.json();
        
        if (data.complete) {
            showCompletion();
        } else {
            displayQuestion(data.question, data.options, data.count);
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
            if (!selectedOption) {
                // Auto-submit with choice "D" or just fail if no choice
                selectedOption = 'A'; // Default skip-like choice for timer end
            }
            submitAnswer();
        }
    }, 1000);
}

function displayQuestion(question, options, count) {
    document.getElementById('question-area').innerText = question;
    document.getElementById('progress-text').innerText = `Question ${count} of 10`;
    
    const grid = document.getElementById('options-grid');
    grid.innerHTML = '';
    
    const labels = ['A', 'B', 'C', 'D'];
    options.forEach((opt, index) => {
        const char = labels[index];
        const card = document.createElement('div');
        card.className = 'option-card';
        card.innerHTML = `<span class="option-indicator">${char}</span> ${opt}`;
        card.onclick = () => selectOption(card, char);
        grid.appendChild(card);
    });
    
    document.getElementById('submit-btn').disabled = true;
}

function selectOption(card, char) {
    if (document.getElementById('explanation-area').style.display !== 'none') return;

    document.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedOption = char;
    document.getElementById('submit-btn').disabled = false;
}

async function submitAnswer() {
    clearInterval(timerInterval);
    const submitBtn = document.getElementById('submit-btn');
    
    submitBtn.disabled = true;
    submitBtn.innerText = "Checking...";
    
    // Disable all options
    document.querySelectorAll('.option-card').forEach(c => c.style.pointerEvents = 'none');
    
    try {
        const response = await fetch('/api/check_aptitude', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: selectedOption })
        });
        const data = await response.json();
        
        showResult(data);
    } catch (e) {
        console.error("Submission error", e);
    } finally {
        submitBtn.innerText = "Submit Answer";
    }
}

function showResult(result) {
    const cards = document.querySelectorAll('.option-card');
    const labels = ['A', 'B', 'C', 'D'];
    
    cards.forEach((card, i) => {
        const char = labels[i];
        if (char === result.correct_answer) {
            card.className = 'option-card correct';
        } else if (char === selectedOption && !result.is_correct) {
            card.className = 'option-card incorrect';
        }
    });

    const expArea = document.getElementById('explanation-area');
    const resultText = document.getElementById('result-text');
    
    expArea.style.display = 'block';
    if (result.is_correct) {
        resultText.innerHTML = '<span style="color: #10b981;"><i class="fa-solid fa-circle-check"></i> Correct!</span>';
    } else {
        resultText.innerHTML = '<span style="color: #ef4444;"><i class="fa-solid fa-circle-xmark"></i> Incorrect</span>';
    }
    
    document.getElementById('explanation-content').innerText = result.explanation;
    expArea.scrollIntoView({ behavior: 'smooth' });
}

function showLoading(isLoading) {
    document.getElementById('loading').style.display = isLoading ? 'block' : 'none';
    document.getElementById('test-container').style.display = isLoading ? 'none' : 'flex';
}

function showCompletion() {
    document.getElementById('test-container').style.display = 'none';
    document.getElementById('completion-area').style.display = 'block';
}
