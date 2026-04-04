import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_remaining_lr():
    ai = AIHandler()
    categories = ["Dice and Cubes", "Syllogism", "Seating Arrangement", "Puzzles"]
    questions = []
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\lr_questions.csv"
    
    print(f"Generating remaining 53 LR questions...")
    
    for category in categories:
        print(f"Generating for {category}...")
        prompt = f"""
        Generate 15 different Logical Reasoning MCQ questions for {category}.
        Format STRICTLY as a JSON array of objects:
        [
          {{
            "type": "lr",
            "category": "{category.lower().replace(' ', '_')}",
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
                            'category': q.get('category', category.lower().replace(' ', '_')),
                            'question': q.get('question', ''),
                            'options': q.get('options', '[]'),
                            'answer': q.get('answer', ''),
                            'difficulty': q.get('difficulty', 'medium'),
                            'explanation': q.get('explanation', '')
                        })
                questions.extend(batch)
                print(f"Added {len(batch)} questions. Total generated in this run: {len(questions)}")
                if len(questions) >= 53: break
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    generate_remaining_lr()
