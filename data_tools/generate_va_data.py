import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_va_questions():
    ai = AIHandler()
    categories = [
        "Synonyms", "Antonyms", "Fill in the Blanks", "Error Detection",
        "Sentence Correction", "Idioms and Phrases", "One Word Substitution",
        "Sentence Completion", "Verbal Analogy", "Spelling Test"
    ]
    difficulties = ["easy", "medium", "hard"]
    
    questions = []
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\va_questions.csv"
    
    # Initialize CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    print(f"Starting VA data generation to {output_path}")
    
    for category in categories:
        # 2 batches of 10 per category = 20 * 10 categories = 200 total
        for i in range(2):
            difficulty = difficulties[(i + (len(questions)//10)) % 3]
            print(f"Generating 10 {difficulty} questions for {category}...")
            prompt = f"""
            Generate 10 different {difficulty} level {category} MCQ Verbal Ability questions.
            Format STRICTLY as a JSON array of objects:
            [
              {{
                "type": "va",
                "category": "{category.lower().replace(' ', '_')}",
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": "...",
                "difficulty": "{difficulty}",
                "explanation": "..."
              }}
            ]
            No extra text, just JSON.
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
                                'type': 'va',
                                'category': q.get('category', category.lower().replace(' ', '_')),
                                'question': q.get('question', ''),
                                'options': q.get('options', '[]'),
                                'answer': q.get('answer', ''),
                                'difficulty': q.get('difficulty', difficulty),
                                'explanation': q.get('explanation', '')
                            })
                    questions.extend(batch)
                    print(f"Added {len(batch)} questions. Total: {len(questions)}")
                else:
                    print(f"Failed to parse batch for {category}")
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(2)
            
    print(f"Done. Generated {len(questions)} questions.")

if __name__ == "__main__":
    generate_va_questions()
