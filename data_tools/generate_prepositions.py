import os
import csv
import json
import time
import sys

# Add parent directory to sys.path to import AIHandler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_handler import AIHandler

def generate_prepositions_batch(batch_size=50, difficulty="easy"):
    handler = AIHandler()
    
    prompt = f"""
    Generate exactly {batch_size} multiple-choice questions for the topic 'Prepositions' in Verbal Ability.
    Difficulty: {difficulty}
    
    DIFFICULTY CRITERIA:
    - Easy: Basic spatial and temporal prepositions (in, on, at, by, to). Simple sentence structures.
    - Medium: Phrasal verbs, prepositions following specific adjectives or verbs (e.g., 'interested in', 'accused of', 'rely on', 'different from'). More complex contexts.
    - Hard: Rare prepositions, tricky nuances (e.g., 'beside' vs 'besides', 'between' vs 'among' in complex cases), prepositions in formal or idiomatic expressions, and sentences where the preposition choice changes the entire meaning. Multiple blanks are encouraged.
    
    Return ONLY a JSON object with a key "questions" containing an array of objects:
    {{
      "questions": [
        {{
          "type": "va",
          "category": "prepositions",
          "question": "The suspect was eventually acquitted ___ all charges due to a lack of evidence.",
          "options": ["A. from", "B. of", "C. off", "D. with"],
          "answer": "B",
          "difficulty": "{difficulty}",
          "explanation": "The verb 'acquitted' is traditionally followed by the preposition 'of'."
        }}
      ]
    }}
    """
    
    try:
        # Use _call_ai which is the internal method for chat completions
        content = handler._call_ai([{"role": "user", "content": prompt}], temperature=0.7, json_mode=True)
        if not content:
            return []
        
        data = json.loads(content)
        return data.get("questions", [])
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []

def main():
    output_path = os.path.join(os.path.dirname(__file__), 'prepositions_questions.csv')
    all_questions = []
    
    difficulties = ["easy", "medium", "hard"]
    questions_per_diff = 50
    batch_size = 25 # Smaller batches are safer for token limits
    
    for diff in difficulties:
        print(f"Generating {questions_per_diff} {diff} questions...")
        count = 0
        while count < questions_per_diff:
            print(f"  Batch {count//batch_size + 1}...")
            batch = generate_prepositions_batch(batch_size, diff)
            if batch:
                all_questions.extend(batch)
                count += len(batch)
                print(f"  Generated {len(batch)} {diff} questions (Total: {count}/{questions_per_diff})")
            else:
                print(f"  Failed to generate batch for {diff}. Retrying...")
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
            # Convert options list to JSON string for CSV storage
            q_copy = q.copy()
            q_copy['options'] = json.dumps(q_copy['options'])
            writer.writerow(q_copy)
            
    print(f"Successfully generated {len(all_questions)} questions and saved to {output_path}")

if __name__ == "__main__":
    main()
