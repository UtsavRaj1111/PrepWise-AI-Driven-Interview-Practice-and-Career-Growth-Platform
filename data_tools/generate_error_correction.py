import os
import csv
import json
import time
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_handler import AIHandler

def generate_ec_batch(batch_size=25, difficulty="easy"):
    handler = AIHandler()
    
    prompt = f"""
    Generate exactly {batch_size} multiple-choice questions for the topic 'Error Correction' in Verbal Ability.
    Difficulty: {difficulty}
    
    DIFFICULTY CRITERIA:
    - Easy: Basic subject-verb agreement, obvious capitalization/spelling errors, simple tense mistakes, and clear plurality errors.
    - Medium: Misplaced modifiers, tricky subject-verb agreement (e.g., collective nouns, 'neither...nor'), incorrect word usage (e.g., 'affect' vs 'effect'), and common idiomatic errors.
    - Hard: Subjunctive mood violations, parallel structure errors in complex multi-clause sentences, dangling participles, subtle tense shifts, and errors in formal register or complex comparison structures.
    
    Format:
    The question should present a sentence with an error, and the options should be possible corrections or identifications of the error.
    Alternatively, a sentence divided into parts where the student identifies which part has the error. 
    Let's stick to identifying the correct version or the part with the error for consistency.
    
    Return ONLY a JSON object with a key "questions" containing an array of objects:
    {{
      "questions": [
        {{
          "type": "va",
          "category": "error_correction",
          "question": "Choose the grammatically correct version of the sentence: 'Between you and I, the plan is bound to fail.'",
          "options": [
            "A. Between you and I, the plan is bound to fail.",
            "B. Between you and me, the plan is bound to fail.",
            "C. Between you and myself, the plan is bound to fail.",
            "D. Between you and me, the plan is bound to failing."
          ],
          "answer": "B",
          "difficulty": "{difficulty}",
          "explanation": "After the preposition 'between', the objective case pronoun 'me' should be used instead of the nominative case 'I'."
        }}
      ]
    }}
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
    output_path = os.path.join(os.path.dirname(__file__), 'error_correction_questions.csv')
    all_questions = []
    
    difficulties = ["easy", "medium", "hard"]
    questions_per_diff = 50
    batch_size = 25
    
    for diff in difficulties:
        print(f"Generating {questions_per_diff} {diff} questions...")
        count = 0
        while count < questions_per_diff:
            print(f"  Batch {count//batch_size + 1}...")
            batch = generate_ec_batch(batch_size, diff)
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
