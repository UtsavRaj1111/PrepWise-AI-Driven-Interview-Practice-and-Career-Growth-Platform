import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIHandler:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")
        
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found. AI features will use placeholders.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def generate_question(self, role, history, difficulty="Intermediate", seed=0):
        """
        Generates an interview question based on the chosen role, history, and current difficulty level.
        """
        if not self.client:
            return f"What are your thoughts on being a {role} at a {difficulty} level?"

        # Build explicit history block to block repeated topics
        history_block = "\n".join([f"- {q}" for q in history]) if history else "None yet."

        prompt = f"""
        Session ID: {seed}. You are a senior technical interviewer at a FAANG-tier company.
        The candidate is applying for: {role}.
        Generate ONE completely new {difficulty} level interview question.
        
        DIFFICULTY GUIDELINES:
        - Junior: Fundamentals, syntax, data structures, basic algorithms.
        - Intermediate: Design patterns, REST APIs, databases, practical coding, debugging.
        - Senior: System design, distributed systems, scalability, architectural trade-offs, leadership.

        QUESTIONS ALREADY ASKED — DO NOT REPEAT OR COVER SIMILAR TOPICS:
        {history_block}

        Choose a DIFFERENT topic area. Be specific, creative, and realistic.
        Output ONLY the question text. No preamble, labels, or explanation.
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=1.2,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Technical Error: {str(e)}"


    def evaluate_answer(self, question, answer, role):
        """
        Full-spectrum evaluation: Technical, Confidence, and Communication scores.
        """
        if not self.client:
            return {
                "score": 7,
                "confidence_score": 6,
                "communication_score": 7,
                "strength": "Good effort on the core concepts.",
                "weakness": "Lacked specific technical details.",
                "suggestion": "Structure your answer using STAR method.",
                "filler_words": "None detected.",
                "clarity_note": "Answer was reasonably clear.",
                "sample_answer": "A more detailed answer would include relevant examples."
            }

        prompt = f"""
        You are an elite technical interviewer AND communication coach at a top-tier company.
        
        Role: {role}
        Question: {question}
        Candidate's Answer: {answer}

        Perform a FULL-SPECTRUM evaluation across three dimensions:

        === DIMENSION 1: TECHNICAL KNOWLEDGE ===
        Evaluate correctness, depth, use of terminology, and completeness.

        === DIMENSION 2: CONFIDENCE ANALYSIS ===
        Analyze the writing for:
        - Hedging / uncertainty language (e.g., "I think", "maybe", "I'm not sure", "I guess")
        - Passive vs active voice
        - Assertiveness of statements
        - Presence of filler phrases

        === DIMENSION 3: COMMUNICATION QUALITY ===
        Analyze:
        - Sentence structure and clarity
        - Logical flow and organization
        - Whether the answer is structured (Intro → Body → Conclusion)
        - Conciseness vs verbosity

        Respond STRICTLY in this format (no extra text):
        Score: [0-10]
        Confidence_Score: [0-10]
        Communication_Score: [0-10]
        Strength: [One specific technical strength]
        Weakness: [One specific technical gap]
        Suggestion: [One actionable improvement]
        Filler_Words: [List any hedging/filler phrases found, or "None detected"]
        Clarity_Note: [One sentence about communication clarity and structure]
        Sample_Answer: [A concise, high-quality model answer]
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            content = chat_completion.choices[0].message.content
            return self._parse_evaluation(content, [
                "score", "confidence_score", "communication_score",
                "strength", "weakness", "suggestion",
                "filler_words", "clarity_note", "sample_answer"
            ])
        except Exception as e:
            return {"error": str(e)}

    def generate_aptitude_question(self, category, difficulty, seed=0):
        """
        Generates an Aptitude or Logical Reasoning question with 4 options.
        Using Chain-of-Thought for mathematical accuracy.
        """
        if not self.client:
            return {
                "question": f"Sample {category} ({difficulty}) question: What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct": "B",
                "explanation": "2 + 2 = 4."
            }

        prompt = f"""
        Session ID: {seed}. You are an expert Aptitude and Psychometric Test designer.
        Generate ONE completely unique {difficulty} level multiple-choice question for {category}.
        
        Be creative and specific. Avoid generic or obvious questions.
        Use varied problem types: word problems, number series, analogies, puzzles, etc.
        
        Return ONLY in this exact structure:
        Question: [The problem statement]
        A: [Option A]
        B: [Option B]
        C: [Option C]
        D: [Option D]
        Correct: [A, B, C, or D]
        Explanation: [Step-by-step logic]
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{{"role": "user", "content": prompt}}],
                model=self.model,
                temperature=1.2,
            )
            content = chat_completion.choices[0].message.content
            return self._parse_evaluation(content, ["question", "a", "b", "c", "d", "correct", "explanation"])
        except Exception as e:
            return {{"error": str(e)}}

    def _parse_evaluation(self, content, expected_keys):
        """
        Enhanced parser to extract evaluation fields reliably.
        """
        result = {}
        lines = content.split('\n')
        current_key = None
        
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip().lower()
                if key in expected_keys:
                    result[key] = parts[1].strip()
                    current_key = key
                    continue
            
            if current_key:
                result[current_key] += " " + line.strip()
        
        # Post-processing — cast all score fields to int
        for score_key in ['score', 'confidence_score', 'communication_score']:
            if score_key in result:
                try:
                    result[score_key] = int(''.join(filter(str.isdigit, str(result[score_key]))))
                    # Clamp to 0-10
                    result[score_key] = max(0, min(10, result[score_key]))
                except:
                    result[score_key] = 5
        
        if 'correct' in result:
            result['correct'] = result['correct'][0].upper() if result['correct'] else 'A'

        # Bundle options for MCQ
        if 'a' in result and 'b' in result:
            result['options'] = [result.get('a'), result.get('b'), result.get('c'), result.get('d')]

        return result

    def analyze_resume(self, resume_text, jd_text=None):
        """
        Section-aware resume analysis. Scans Education, Skills, Experience,
        Projects, Certifications individually. Uses Groq JSON mode for
        guaranteed valid output. ATS score is always content-driven.
        """
        import json

        resume_snippet = resume_text[:3500].strip()
        jd_snippet     = jd_text[:1500].strip() if jd_text else ""

        # Debug: confirm actual content is being passed
        print(f"\n[Resume Analyzer] Resume chars: {len(resume_snippet)}, JD chars: {len(jd_snippet)}")
        print(f"[Resume Analyzer] First 200 chars: {resume_snippet[:200]}")

        abbrev_note = (
            "NOTE: These abbreviations are equivalent — treat either form as the same skill present: "
            "ML=Machine Learning, DL=Deep Learning, NLP=Natural Language Processing, AI=Artificial Intelligence, "
            "LLM=Large Language Model, JS=JavaScript, TS=TypeScript, SQL=Structured Query Language, "
            "AWS=Amazon Web Services, GCP=Google Cloud Platform, k8s=Kubernetes, CI/CD=Continuous Integration, "
            "OOP=Object-Oriented Programming, DSA=Data Structures and Algorithms, REST=RESTful API, "
            "UI=User Interface, UX=User Experience, QA=Quality Assurance, DS=Data Science."
        )

        jd_instruction = f"""
COMPARE AGAINST THIS JOB DESCRIPTION:
{jd_snippet}

{abbrev_note}
Mark a keyword as missing ONLY if it appears in the JD but does NOT appear in the resume in ANY form (acronym or full name).
""" if jd_snippet else "No JD provided — give a general professional ATS critique."

        # ── CALL 1: EXTRACT facts (low temp = precise, literal extraction) ──
        extract_prompt = f"""You are a resume parser. Extract ONLY what you literally read in the resume text.
Do not infer or guess anything — only report explicitly written content.

RESUME TEXT:
---
{resume_snippet}
---

Return ONLY this JSON:
{{
  "name": "<full name if found, else empty string>",
  "email": "<email if found, else empty string>",
  "phone": "<phone if found, else empty string>",
  "linkedin": "<LinkedIn URL/username if found, else empty string>",
  "github": "<GitHub URL/username if found, else empty string>",
  "degree": "<degree + field, e.g. B.Tech Computer Science>",
  "institution": "<college or university name>",
  "grad_year": "<graduation or expected year>",
  "skills": ["<exact technology/skill named>", "<skill>", "<skill>", "<skill>", "<skill>", "<skill>"],
  "experience": [
    {{"company": "<company name>", "role": "<role title>", "duration": "<time period>"}}
  ],
  "projects": [
    {{"name": "<project name>", "tech": "<tech stack used>", "outcome": "<result or description if present, else empty string>"}}
  ],
  "certifications": ["<certification name if listed>"],
  "has_numbers": <true if ANY bullet point contains a number, %, or $ metric>,
  "has_action_verbs": <true if bullets use words like Built/Designed/Developed/Led/Implemented>
}}"""

        # ── CALL 2: SCORE from structured facts + JD ─────────────────────
        jd_compare_block = ""
        if jd_snippet:
            jd_compare_block = f"""
JOB DESCRIPTION (to compare for match_percent):
---
{jd_snippet}
---
ABBREVIATION RULES: {abbrev_note}

To calculate match_percent:
1. List every distinct skill/technology/keyword from the JD.
2. For each, check if it appears in the candidate's skills list OR anywhere in the resume text (use abbreviation rules).
3. match_percent = round((matched count / total JD keywords) * 100)
"""

        score_prompt_template = """You are an ATS scoring engine. Use the extracted resume data below to compute accurate scores.

EXTRACTED RESUME FACTS:
{extracted}

RESUME TEXT (for keyword search):
---
{resume}
---

{jd_block}

COMPUTE ats_score by adding points for each criterion:
- has_numbers=true → +18 pts
- has_action_verbs=true → +12 pts  
- len(skills) >= 5 → +15 pts | len(skills) >= 3 → +8 pts
- len(experience) >= 2 → +20 pts | len(experience) == 1 → +12 pts
- len(projects) >= 3 → +20 pts | len(projects) == 2 → +13 pts | len(projects) == 1 → +7 pts
- degree AND institution both non-empty → +10 pts
- email present AND (phone OR linkedin OR github non-empty) → +7 pts
- len(certifications) >= 1 → +5 pts
Cap final score at 100.

Return ONLY valid JSON:
{{
  "ats_score": <integer 0-100>,
  "match_percent": <integer 0-100, 0 if no JD>,
  "summary": "<2-3 sentences naming REAL content: actual projects, actual companies, actual degree>",
  "education_note": "<degree + institution + year, or 'Not specified' if absent>",
  "skills_found": ["<skill1>", "<skill2>", "<skill3>", "<skill4>", "<skill5>", "<skill6>"],
  "projects_found": [
    {{"name": "<project name>", "tech": "<tech stack>", "outcome": "<outcome or brief description>"}},
    {{"name": "<project name>", "tech": "<tech stack>", "outcome": "<outcome>"}}
  ],
  "strengths": [
    "<specific strength based on what the extracted data shows>",
    "<second strength>",
    "<third strength>"
  ],
  "weaknesses": [
    "<real gap: e.g. has_numbers=false means no quantified achievements>",
    "<second gap>",
    "<third gap>"
  ],
  "missing_keywords": ["<JD keyword not matched in any form>", "<keyword>"],
  "improvements": [
    "<actionable bullet rewrite, e.g. change vague bullets to 'Built X reducing Y by Z%'>",
    "<second fix>",
    "<third fix>"
  ]
}}"""

        # ── CALL 3: Tailored interview questions ───────────────────────────
        questions_prompt = f"""You are a FAANG technical interviewer. Study this resume and write 5 targeted questions.
Each question MUST reference a specific project, skill, or experience from their resume.

RESUME:
---
{resume_snippet[:2000]}
---

Return ONLY this JSON:
{{
  "questions": [
    "<question about a specific project by name>",
    "<question about a technology they listed>",
    "<situational question based on their internship/experience>",
    "<deep-dive on a specific project outcome>",
    "<question about their education or certifications>"
  ]
}}"""

        try:
            import json as _json

            # Call 1: Extract (very low temp for accuracy)
            print("[Resume Analyzer] Call 1: Extracting facts...")
            r1 = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": extract_prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            extracted_raw = r1.choices[0].message.content
            print(f"[Resume Analyzer] Extracted: {extracted_raw[:200]}")

            # Call 2: Score (moderate temp — creative but consistent)
            print("[Resume Analyzer] Call 2: Scoring...")
            score_prompt = score_prompt_template.format(
                extracted=extracted_raw,
                resume=resume_snippet,
                jd_block=jd_compare_block
            )
            r2 = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": score_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            analysis = _json.loads(r2.choices[0].message.content)
            print(f"[Resume Analyzer] Score result: ATS={analysis.get('ats_score')}, JD={analysis.get('match_percent')}")

            # Call 3: Questions (high temp for variety)
            print("[Resume Analyzer] Call 3: Questions...")
            r3 = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": questions_prompt}],
                temperature=0.9,
                response_format={"type": "json_object"},
            )
            q_data = _json.loads(r3.choices[0].message.content)
            analysis["questions"] = q_data.get("questions", [])

            result = self._fill_resume_defaults(analysis)
            print(f"[Resume Analyzer] ✅ ATS={result['ats_score']}, JD={result['match_percent']}, Projects={len(result.get('projects_found', []))}, Q={len(result['questions'])}")
            return result

        except Exception as e:
            print(f"[Resume Analyzer] ERROR: {e}")
            import traceback; traceback.print_exc()
            return {"error": f"AI analysis failed: {str(e)}"}


    def _parse_resume_analysis(self, content):
        import json, re

        # Strategy 1: Extract JSON from markdown code fence
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if fence_match:
            try:
                data = json.loads(fence_match.group(1))
                return self._fill_resume_defaults(data)
            except:
                pass

        # Strategy 2: Find the largest {...} block
        brace_match = re.search(r'\{.*\}', content, re.DOTALL)
        if brace_match:
            try:
                data = json.loads(brace_match.group())
                return self._fill_resume_defaults(data)
            except:
                pass

        # Strategy 3: Try parsing the whole content
        try:
            data = json.loads(content.strip())
            return self._fill_resume_defaults(data)
        except:
            pass

        # Fallback: return a diagnostic response
        print(f"Resume parse failed. Raw content preview: {content[:300]}")
        return {
            "ats_score": 0,
            "match_percent": 0,
            "summary": "Analysis completed but response format was unexpected. The AI produced a non-JSON response. Please try again.",
            "strengths": [],
            "weaknesses": ["Could not parse detailed results — please re-upload and try again."],
            "missing_keywords": [],
            "improvements": ["Ensure your PDF is text-based (not scanned image) for best results."],
            "questions": []
        }

    def _fill_resume_defaults(self, data):
        """Ensure all expected keys exist in parsed resume analysis."""
        defaults = {
            "ats_score": 0,
            "match_percent": 0,
            "summary": "Analysis complete.",
            "education_note": "",
            "skills_found": [],
            "projects_found": [],
            "strengths": [],
            "weaknesses": [],
            "missing_keywords": [],
            "improvements": [],
            "questions": []
        }
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        # Clamp scores
        data['ats_score']     = max(0, min(100, int(data.get('ats_score', 0))))
        data['match_percent'] = max(0, min(100, int(data.get('match_percent', 0))))
        return data


    def get_mentor_response(self, user_message, chat_history, file_context=None):
        """
        AI Career Mentor logic. Provides guidance and answers questions.
        Supports optional file-based context (PDF/OCR content).
        """
        history_context = ""
        # Format history for prompt
        for msg in chat_history[-6:]:  # Keep last 6 messages for context
            role = "Mentor" if msg['role'] == 'assistant' else "User"
            history_context += f"{role}: {msg['content']}\n"

        file_block = ""
        if file_context:
            file_block = f"""
            [ATTACHED FILE CONTEXT]:
            {file_context}
            ---
            The user has uploaded a document/data. Prioritize analyzing this content if the user's message refers to it.
            """

        prompt = f"""
        You are 'PrepWise AI Mentor', an elite career coach and technical expert.
        
        {file_block}

        GOALS:
        1. Help with Interview Prep (Technical, Behavioral, Case).
        2. Answer deep technical questions (Web, ML, Cloud, DSA).
        3. Provide Career Strategy (Job Search, Resume tips, Salary negotiations).
        
        CURRENT CONVERSATION HISTORY:
        {history_context}
        
        USER'S NEW MESSAGE:
        {user_message}
        
        RESPONSE GUIDELINES:
        - Be encouraging, concise, and professional.
        - Use Markdown (bolding, bullet points) for readability.
        - If the user asks for a mockup interview, suggest a role to start with.
        - Provide actionable advice.
        - Keep responses focused on career and technical growth.
        """

        try:
            if not self.client:
                return f"I've received your signal regarding '{user_message[:30]}...'. Currently, my neural processing units are operating in offline mode. Please ensure your Groq API key is active for full PrepWise guidance!"

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Mentor AI error: {e}")
            return "Apologies, I encountered a brief technical hiccup. Could you please rephrase your request?"
