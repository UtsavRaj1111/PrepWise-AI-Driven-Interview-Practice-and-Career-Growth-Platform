import os
import csv
import json
import time
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_handler import AIHandler

def generate_es_batch(batch_size=25, difficulty="easy"):
    handler = AIHandler()
    
    prompt = f"""
    Generate exactly {batch_size} multiple-choice questions for the topic 'Error Spotting' in Verbal Ability.
    Difficulty: {difficulty}
    
    DIFFICULTY CRITERIA:
    - Easy: Simple grammatical errors like subject-verb agreement (singular/plural), basic tense inconsistencies, or obvious article usage mistakes.
    - Medium: Tricky subject-verb agreement (collective nouns, 'either...or'), incorrect preposition usage, common word confusion (its/it's, their/there), and basic parallel structure issues.
    - Hard: Subtle errors in subjunctive mood, complex comparison structures, misplaced/dangling modifiers in multi-clause sentences, nuances of formal vs informal grammar, and hidden redundancies.

    FORMAT:
    The question MUST present a sentence divided into exactly 3 parts by slashes (/).
    The options MUST correspond to these parts plus a 'No Error' option.
    
    Example:
    Question: "The team / have reached / a unanimous decision."
    Option A: "The team"
    Option B: "have reached"
    Option C: "a unanimous decision"
    Option D: "No Error"
    Answer: B
    Explanation: "The word 'team' is a collective noun and should take a singular verb 'has' in this context of a unanimous decision."

    Return ONLY a JSON object with a key "questions" containing an array of objects:
    {{
      "questions": [
        {{
          "type": "va",
          "category": "error_spotting",
          "question": "Identify the part that contains a grammatical error: 'The team / have reached / a unanimous decision.'",
          "options": [
            "The team",
            "have reached",
            "a unanimous decision",
            "No Error"
          ],
          "answer": "B",
          "difficulty": "{difficulty}",
          "explanation": "The word 'team' is a collective noun and should take a singular verb 'has' in this context of a unanimous decision."
        }}
      ]
    }}
    Ensure options are plain strings (no A. B. C. D. prefixes).
    """
    
    try:
        content = handler._call_ai([{"role": "user", "content": prompt}], temperature=0.7, json_mode=True)
        if not content:
            return []
        
        data = json.loads(content)
        return data.get("questions", [])
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []

def main():
    output_path = os.path.join(os.path.dirname(__file__), 'error_spotting_questions.csv')
    all_questions = []
    
    difficulties = ["easy", "medium", "hard"]
    questions_per_diff = 50
    batch_size = 25
    
    for diff in difficulties:
        print(f"Generating {questions_per_diff} {diff} questions...")
        count = 0
        while count < questions_per_diff:
            print(f"  Batch {count//batch_size + 1}...")
            batch = generate_es_batch(batch_size, diff)
            if batch:
                all_questions.extend(batch)
                count += len(batch)
                print(f"  Generated {len(batch)} {diff} questions (Total: {count}/{questions_per_diff})")
            else:
                print(f"  Failed to generate batch. Retrying...")
                time.sleep(5)
            time.sleep(2)
            
    if not all_questions:
        print("No questions generated.")
        return

    # Write to CSV (overwrite)
    keys = ["type", "category", "question", "options", "answer", "difficulty", "explanation"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for q in all_questions:
            q_copy = q.copy()
            if isinstance(q_copy.get('options'), list):
                q_copy['options'] = json.dumps(q_copy['options'])
            writer.writerow(q_copy)
            
    print(f"Successfully generated {len(all_questions)} questions and saved to {output_path}")

if __name__ == "__main__":
    main()
