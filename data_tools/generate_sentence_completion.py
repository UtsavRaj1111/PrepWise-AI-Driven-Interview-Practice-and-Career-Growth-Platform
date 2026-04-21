import os
import csv
import json
import time
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_handler import AIHandler

def generate_sc_batch(batch_size=25, difficulty="easy"):
    handler = AIHandler()
    
    prompt = f"""
    Generate exactly {batch_size} multiple-choice questions for the topic 'Sentence Completion' in Verbal Ability.
    Difficulty: {difficulty}
    
    DIFFICULTY CRITERIA:
    - Easy: Single-blank sentences with common vocabulary. The context provides clear, direct clues to the missing word.
    - Medium: Single or double-blank sentences. Involves logical connectors like 'however', 'moreover', or 'consequently'. Vocabulary is intermediate (college level).
    - Hard: Double-blank sentences with sophisticated vocabulary (GRE/GMAT level). Requires understanding subtle nuances, tone, and complex logical relationships (e.g., paradoxical or ironic contexts).
    
    Format:
    The question should be a sentence with one or two blanks (represented by '___').
    The options (A, B, C, D) should be words or pairs of words.
    
    Return ONLY a JSON object with a key "questions" containing an array of objects:
    {{
      "questions": [
        {{
          "type": "va",
          "category": "sentence_completion",
          "question": "Despite the ___ of the evidence, the jury remained ___ about the defendant's guilt.",
          "options": [
            "A. weight, skeptical",
            "B. paucity, convinced",
            "C. abundance, certain",
            "D. lack, dubious"
          ],
          "answer": "A",
          "difficulty": "{difficulty}",
          "explanation": "'Despite' indicates a contrast. If the evidence was heavy (weight), one would expect conviction, but the jury was 'skeptical' (contrast)."
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
    output_path = os.path.join(os.path.dirname(__file__), 'sentence_completion_questions.csv')
    all_questions = []
    
    difficulties = ["easy", "medium", "hard"]
    questions_per_diff = 50
    batch_size = 25
    
    for diff in difficulties:
        print(f"Generating {questions_per_diff} {diff} questions...")
        count = 0
        while count < questions_per_diff:
            print(f"  Batch {count//batch_size + 1}...")
            batch = generate_sc_batch(batch_size, diff)
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
