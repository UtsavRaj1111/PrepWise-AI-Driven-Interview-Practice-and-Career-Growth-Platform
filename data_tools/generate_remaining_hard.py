import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_remaining_hard_questions():
    ai = AIHandler()
    categories = [
        "Permutations and Combinations", "Logic Puzzles"
    ]
    
    questions = []
    
    for category in categories:
        print(f"Generating remaining HARD questions for: {category}")
        prompt = f"""
        Generate 10 different HARD level {category} MCQ aptitude questions.
        Format STRICTLY as a JSON array:
        [
          {{
            "type": "aptitude",
            "category": "{category.lower().replace(' ', '_')}",
            "question": "...",
            "options": ["...", "...", "...", "..."],
            "answer": "...",
            "difficulty": "hard",
            "explanation": "..."
          }}
        ]
        """
        try:
            response = ai.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            batch = json.loads(response.choices[0].message.content)
            if isinstance(batch, dict) and "questions" in batch:
                batch = batch["questions"]
            elif isinstance(batch, dict) and len(batch) == 1:
                batch = list(batch.values())[0]
            
            if isinstance(batch, list):
                questions.extend(batch)
        except Exception as e:
            print(f"Error: {e}")
            
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\hard_aptitude_questions.csv"
    # Append to existing file
    with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for q in questions:
            if isinstance(q.get('options'), list):
                q['options'] = json.dumps(q['options'])
            writer.writerow({
                'type': 'aptitude',
                'category': q.get('category', 'general'),
                'question': q.get('question', ''),
                'options': q.get('options', '[]'),
                'answer': q.get('answer', ''),
                'difficulty': 'hard',
                'explanation': q.get('explanation', '')
            })

if __name__ == "__main__":
    generate_remaining_hard_questions()
