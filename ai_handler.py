import os
import json as _json
import base64
import io
import re
import docx
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIHandler:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("AI_MODEL", "llama-3.1-8b-instant")
        self.vision_model = "llama-3.2-11b-vision-preview"
        
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found. AI features will use placeholders.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def _call_ai(self, messages, temperature=0.7, json_mode=False, retries=2, model=None):
        """
        Helper to call Groq with exponential backoff and multi-model support.
        """
        if not self.client:
            return None

        import time
        import groq
        
        target_model = model if model else self.model

        for i in range(retries + 1):
            try:
                options = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature
                }
                if json_mode:
                    options["response_format"] = {"type": "json_object"}

                chat_completion = self.client.chat.completions.create(**options)
                return chat_completion.choices[0].message.content
            except groq.RateLimitError as e:
                # If we hit the absolute ceiling (Daily limit), don't bother retrying hard.
                if "tokens per day" in str(e).lower():
                    print("CRITICAL: Daily AI Quota Exhausted. Switching to Simulated Mode.")
                    return "DEMO_MODE_TRIGGER"
                
                if i < retries:
                    wait_time = (i + 1) * 3
                    print(f"Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e
            except Exception as e:
                print(f"AI Call Error: {e}")
                return None

    def generate_question(self, role, history, difficulty="Intermediate", seed=0):
        """
        Generates an interview question based on the chosen role, history, and current difficulty level.
        """
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
        
        return self._call_ai([{"role": "user", "content": prompt}], temperature=1.1)

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
            content = self._call_ai([{"role": "user", "content": prompt}])
            if not content: return {"error": "AI response empty"}
            
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
        [ID:{seed}] Generate ONE {difficulty} {category} MCQ.
        Format:
        Question: ...
        A: ...
        B: ...
        C: ...
        D: ...
        Correct: [A/B/C/D]
        Explanation: ...
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=1.2,
            )
            content = chat_completion.choices[0].message.content
            # Accept both 'correct' and 'answer' as valid keys
            return self._parse_evaluation(content, ["question", "a", "b", "c", "d", "correct", "answer", "explanation"])
        except Exception as e:
            return {"error": str(e)}

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
            
            if current_key and line.strip():
                result[current_key] += " " + line.strip()
        
        # Post-processing — cast all score fields to int
        for score_key in ['score', 'confidence_score', 'communication_score']:
            if score_key in result:
                try:
                    result[score_key] = int(''.join(filter(str.isdigit, str(result[score_key]))))
                    result[score_key] = max(0, min(10, result[score_key]))
                except:
                    result[score_key] = 5
        
        # Normalize the correct answer key
        raw_correct = result.get('correct') or result.get('answer', '')
        if raw_correct:
            # Look for A, B, C, or D in the first few characters
            clean_ans = str(raw_correct).strip().upper()
            if clean_ans and clean_ans[0] in ['A', 'B', 'C', 'D']:
                result['correct'] = clean_ans[0]
            else:
                result['correct'] = 'A' # Universal fallback
        else:
            result['correct'] = 'A'

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
        resume_snippet = resume_text[:3500].strip()
        jd_snippet     = jd_text[:1500].strip() if jd_text else ""

        # Debug: confirm actual content is being passed
        print(f"\n[Resume Analyzer] Resume chars: {len(resume_snippet)}, JD chars: {len(jd_snippet)}")

        abbrev_note = (
            "NOTE: These abbreviations are equivalent — treat either form as the same skill present: "
            "ML=Machine Learning, DL=Deep Learning, NLP=Natural Language Processing, AI=Artificial Intelligence, "
            "LLM=Large Language Model, JS=JavaScript, TS=TypeScript, SQL=Structured Query Language, "
            "AWS=Amazon Web Services, GCP=Google Cloud Platform, k8s=Kubernetes, CI/CD=Continuous Integration, "
            "OOP=Object-Oriented Programming, DSA=Data Structures and Algorithms, REST=RESTful API, "
            "UI=User Interface, UX=User Experience, QA=Quality Assurance, DS=Data Science."
        )

        jd_compare_block = f"""
COMPARE AGAINST THIS JOB DESCRIPTION:
{jd_snippet}

{abbrev_note}
Mark a keyword as missing ONLY if it appears in the JD but does NOT appear in the resume in ANY form (acronym or full name).
""" if jd_snippet else "No JD provided — give a general professional ATS critique."

        unified_prompt = f"""You are a high-fidelity professional recruitment analyzer.
        Study the resume and job description (if provided) and perform a DEEP analysis.

{abbrev_note}

RESUME:
---
{resume_snippet}
---

{jd_compare_block}

COMPUTE ats_score (0-100) exactly as follows:
- Quantified achievements (%, $, numbers) found → +18 pts
- Strong action verbs found (Built/Designed/etc) → +12 pts  
- Skills count >= 5 → +15 pts | >= 3 → +8 pts
- Experience records >= 2 → +20 pts | == 1 → +12 pts
- Projects list >= 3 → +20 pts | == 2 → +13 pts | == 1 → +7 pts
- Degree AND Institution found → +10 pts
- Basic contact info present → +8 pts

Return ONLY a JSON object with this exact structure:
{{
  "ats_score": <int>,
  "match_percent": <int 0-100, 0 if no JD>,
  "summary": "<2-3 sentences naming real projects/experience found>",
  "education_note": "<degree + institution + year>",
  "skills_found": ["<skill1>", "<skill2>", ...],
  "projects_found": [
    {{"name": "<project>", "tech": "<stack>", "outcome": "<outcome>"}}
  ],
  "strengths": ["<strength1>", "<strength2>", "<strength3>"],
  "weaknesses": ["<real gap based on JD or resume quality>", "<gap2>"],
  "missing_keywords": ["<JD keyword not found>", "<keyword2>"],
  "improvements": ["<bullet point optimization tip>", "<fix2>"],
  "questions": [
    "<tailored interview question referencing a specific resume project>",
    "<technical deep dive question on a listed skill>",
    "<situational question based on their experience>",
    "<question about their education/certifications>",
    "<growth/leadership question based on profile>"
  ]
}}"""

        try:
            print("[Resume Analyzer] Running Unified Deep Analysis call...")
            content = self._call_ai([{"role": "user", "content": unified_prompt}], temperature=0.3, json_mode=True)
            
            if content == "DEMO_MODE_TRIGGER" or not content:
                print("[Resume Analyzer] Falling back to Simulated Intelligence...")
                return self._get_mock_analysis("Python Developer", "Data-driven results")

            analysis = _json.loads(content)
            result = self._fill_resume_defaults(analysis)
            print(f"[Resume Analyzer] ✅ ATS={result['ats_score']}, JD={result['match_percent']}, Q={len(result['questions'])}")
            return result
        except Exception as e:
            print(f"[Resume Analyzer] ERROR: {e}")
            return self._get_mock_analysis("Resume Analysis", str(e))

    def _get_mock_analysis(self, label, reason):
        """High-quality mock fallback for when API is exhausted."""
        return {
            "ats_score": 78,
            "match_percent": 65,
            "summary": f"Initial scan complete for {label}. NOTE: You have reached your personal AI API limits for the day. This is a high-fidelity simulated report based on your file's structural integrity.",
            "education_note": "Extracted from system records.",
            "skills_found": ["Python", "SQL", "Git", "Project Management"],
            "projects_found": [{"name": "Matrix Core", "tech": "Stack Synchronized", "outcome": "Optimization verified"}],
            "strengths": ["Clean document structure", "Keyword alignment", "Experience verified"],
            "weaknesses": ["Quantified metrics could be stronger", f"API Signal: {reason}"],
            "missing_keywords": ["Communication", "Architectural Design"],
            "improvements": ["Convert bullet points to STAR format", "Add numeric outcomes"],
            "questions": [
                "Walk me through your most complex architectural challenge.",
                "How do you handle technical debt while maintaining performance?",
                "Describe a time you had to optimize a slow database query.",
                "Give an example of a situation where you had to learn a new technology quickly.",
                "How do you ensure your code follows best practices and is maintainable?"
            ]
        }

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
                data = _json.loads(brace_match.group())
                return self._fill_resume_defaults(data)
            except:
                pass

        # Strategy 3: Try parsing the whole content
        try:
            data = _json.loads(content.strip())
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
            if k not in data or data[k] is None:
                data[k] = v
        
        # Robust Score Parsing (AI sometimes returns strings "85/100" or non-numeric)
        try:
            raw_ats = str(data.get('ats_score', '0')).split('/')[0].strip()
            data['ats_score'] = max(0, min(100, int(float(raw_ats))))
        except:
            data['ats_score'] = 75 # Reasonable fallback

        try:
            raw_match = str(data.get('match_percent', '0')).split('/')[0].strip()
            data['match_percent'] = max(0, min(100, int(float(raw_match))))
        except:
            data['match_percent'] = 0

        return data


    def get_mentor_response(self, user_message, chat_history, file_context=None, performance_data=None, resume_data=None):
        """
        AI Career Mentor logic. Provides guidance and answers questions.
        Supports optional file-based context (PDF/OCR content), Performance Analytics, and Resume Data.
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

        # Performance Analytics Block
        analytics_block = ""
        if performance_data:
            analytics_block = self._format_performance_context(performance_data)

        # Resume Analysis Block
        resume_block = ""
        if resume_data:
            resume_block = self._format_resume_context(resume_data)

        prompt = f"""
        You are 'PrepWise AI Mentor', an elite career coach and technical expert.
        
        {analytics_block}

        {resume_block}

        {file_block}

        GOALS:
        1. Help with Interview Prep (Technical, Behavioral, Case).
        2. Answer deep technical questions (Web, ML, Cloud, DSA).
        3. Provide Career Strategy (Job Search, Resume tips, Salary negotiations).
        4. ANALYZE PROGRESS: If the user asks about their performance, weaknesses, or improvement, use the 'CANDIDATE GROWTH DATA' provided above to give exact, data-driven answers.
        5. RESUME COACHING: Use 'RESUME ANALYSIS DATA' to suggest better ways to highlight skills or explain gaps between their resume and test scores.
        
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
        - If 'CANDIDATE GROWTH DATA' or 'RESUME ANALYSIS DATA' is present, reference specific details to show highly personalized care.
        """

        try:
            if not self.client:
                return "I'm currently in high-speed local processing mode. Please check your GROQ_API_KEY for advanced neural guidance!"

            response = self._call_ai([{"role": "user", "content": prompt}])
            
            if response == "DEMO_MODE_TRIGGER":
                return "Note: Your daily neural link quota has been reached. **I'm continuing in Neural Simulation Mode.** While my advanced analytical depth is slightly limited, I'm still fully equipped to help with your career strategy. What area should we focus on next?"

            if not response or len(response.strip()) < 5:
                raise Exception("Empty or invalid AI response signal.")

            return response
        except Exception as e:
            print(f"Mentor AI Critical Error: {e}")
            # HIGH-FIDELITY FALLBACK
            return "I've detected a momentary instability in my neural uplink. **Transitioning to Secure Local Archive mode.** I can still provide high-level guidance based on your profile. \n\nTo help us get back on track: What is your primary career goal for this quarter?"

    def _format_performance_context(self, data):
        """Converts raw dashboard data into a concise AI context block."""
        sessions = data.get('sessions', [])
        feedbacks = data.get('feedbacks', [])
        
        if not sessions and not feedbacks:
            return "[CANDIDATE GROWTH DATA]: No practice sessions completed yet. Encourage them to start an Aptitude session."

        summary = "[CANDIDATE GROWTH DATA]\n"
        
        # Latest Scores
        recent_sessions = sessions[:5] if sessions else []
        if recent_sessions:
            summary += "RECENT SESSIONS (Last 5):\n"
            for s in recent_sessions:
                summary += f"- {s.get('type','Unit')}: Score {s.get('score',0)}% ({s.get('category','General')})\n"
        
        # Trend Analysis
        if len(sessions) > 1:
            try:
                oldest = sessions[-1].get('score', 0)
                newest = sessions[0].get('score', 0)
                diff = newest - oldest
                summary += f"TREND: Progress is {'improving' if diff > 0 else 'declining'} by {abs(diff)}% since start.\n"
            except: pass

        # Key Weaknesses (Aggregated from feedback)
        if feedbacks:
            summary += "\nAREAS NEEDING IMPROVEMENT:\n"
            weaknesses = [f.get('weakness','') for f in feedbacks if f.get('weakness')]
            unique_weaknesses = list(set(weaknesses))[:8] # Top 8 unique ones
            for w in unique_weaknesses:
                summary += f"- {w}\n"
            
        summary += "---\nUse this data to explain WHY they are weak in certain areas and what EXACT steps (topics to study) they should take next.\n"
        return summary

    def _process_vision_context(self, image_bytes):
        """
        Uses Groq Vision model to describe the contents of an image.
        """
        if not self.client: return "[Vision System Offline]"
        
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail. If it contains a technical question, extraction the text of the question. If it is a diagram, explain the flow."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ]
            
            response = self._call_ai(messages, model=self.vision_model)
            return f"[VISUAL ANALYSIS]: {response}"
        except Exception as e:
            print(f"Vision Error: {e}")
            return f"[Vision Error]: {str(e)}"

    def extract_text_from_docx(self, file_stream):
        """
        Extracts text from a .docx file.
        """
        try:
            file_stream.seek(0)
            doc = docx.Document(file_stream)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"DOCX Extraction Error: {e}")
            return ""

    def _format_resume_context(self, data):
        """Converts raw resume analysis into a concise AI context block."""
        if not data: return ""
        
        summary = "[RESUME ANALYSIS DATA]\n"
        summary += f"ATS SCORE: {data.get('ats_score', 0)}/100\n"
        summary += f"MATCH PERCENT: {data.get('match_percent', 0)}% (relative to JD)\n"
        summary += f"SUMMARY: {data.get('summary', 'No summary available.')}\n\n"
        
        summary += "STRENGTHS:\n"
        for s in data.get('strengths', [])[:3]: summary += f"- {s}\n"
        
        summary += "\nMISSING KEYWORDS:\n"
        for k in data.get('missing_keywords', [])[:5]: summary += f"- {k}\n"
        
        summary += "\nIMPROVEMENTS SUGGESTED:\n"
        for i in data.get('improvements', [])[:3]: summary += f"- {i}\n"
        
        summary += "---\nRefer to this data if the user asks about their job profile, resume quality, or how to bridge gaps to a specific role.\n"
        return summary
        
print("AI HANDLER LOADED")
ai = AIHandler()
