import os
import csv
import json
import time
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_handler import AIHandler

def generate_pj_batch(batch_size=25, difficulty="easy"):
    handler = AIHandler()
    
    prompt = f"""
    Generate exactly {batch_size} multiple-choice questions for the topic 'Para Jumbles' in Verbal Ability.
    Difficulty: {difficulty}
    
    DIFFICULTY CRITERIA:
    - Easy: 3-4 short sentences with very clear logical or chronological connectors (e.g., 'First', 'Next', 'Finally'). The flow is straightforward.
    - Medium: 4-5 sentences with less obvious transitions. Requires identifying pronoun references (e.g., 'This', 'They') and general-to-specific logical flow.
    - Hard: 5-6 complex sentences on academic, technical, or philosophical topics. Subtle transitions and abstract concepts. Several sequences might seem plausible, but only one is logically consistent.
    
    Format:
    The question should list the sentences (labeled 1, 2, 3, etc.) in a jumbled order.
    The options (A, B, C, D) should be different numerical sequences (e.g., '3-1-4-2').
    
    Return ONLY a JSON object with a key "questions" containing an array of objects:
    {{
      "questions": [
        {{
          "type": "va",
          "category": "para_jumbles",
          "question": "Arrange the following sentences in a logical order:\\n1. Then, he decided to go for a walk.\\n2. John woke up early in the morning.\\n3. After his walk, he prepared a healthy breakfast.",
          "options": [
            "A. 2-1-3",
            "B. 1-2-3",
            "C. 3-2-1",
            "D. 2-3-1"
          ],
          "answer": "A",
          "difficulty": "{difficulty}",
          "explanation": "Sentence 2 sets the scene (waking up), sentence 1 follows with the first action (walk), and sentence 3 concludes after the walk (breakfast)."
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
    output_path = os.path.join(os.path.dirname(__file__), 'para_jumbles_questions.csv')
    all_questions = []
    
    difficulties = ["easy", "medium", "hard"]
    questions_per_diff = 50
    batch_size = 15 # PJ questions are longer, so smaller batches for token limits
    
    for diff in difficulties:
        print(f"Generating {questions_per_diff} {diff} questions...")
        count = 0
        while count < questions_per_diff:
            print(f"  Batch {count//batch_size + 1}...")
            batch = generate_pj_batch(batch_size, diff)
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
