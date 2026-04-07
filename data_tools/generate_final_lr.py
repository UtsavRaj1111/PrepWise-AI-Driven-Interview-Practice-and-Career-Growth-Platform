import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_final_15():
    ai = AIHandler()
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\lr_questions.csv"
    
    print(f"Generating final 15 questions...")
    prompt = f"""
    Generate 15 different Medium level Coding-Decoding Logical Reasoning MCQ questions.
    Format STRICTLY as a JSON array of objects:
    [
      {{
        "type": "lr",
        "category": "coding_decoding",
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "answer": "...",
        "difficulty": "medium",
        "explanation": "..."
      }}
    ]
    """
    try:
        response = ai.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        batch = json.loads(response.choices[0].message.content)
        if isinstance(batch, dict):
            if "questions" in batch: batch = batch["questions"]
            elif len(batch) == 1: batch = list(batch.values())[0]
        
        if isinstance(batch, list):
            with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation'])
                for q in batch:
                    if isinstance(q.get('options'), list):
                        q['options'] = json.dumps(q['options'])
                    writer.writerow({
                        'type': 'lr',
                        'category': 'coding_decoding',
                        'question': q.get('question', ''),
                        'options': q.get('options', '[]'),
                        'answer': q.get('answer', ''),
                        'difficulty': 'medium',
                        'explanation': q.get('explanation', '')
                    })
            print(f"Added {len(batch)} final questions.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_final_15()
