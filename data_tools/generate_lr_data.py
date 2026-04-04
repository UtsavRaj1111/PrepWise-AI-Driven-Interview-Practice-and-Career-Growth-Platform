import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_lr_questions():
    ai = AIHandler()
    categories = [
        "Syllogism", "Blood Relations", "Coding Decoding", "Number Series",
        "Letter Series", "Analogy", "Classification", "Direction Sense",
        "Seating Arrangement", "Ranking and Order", "Puzzles", "Venn Diagrams",
        "Dice and Cubes", "Statements and Assumptions", "Statements and Conclusions"
    ]
    difficulties = ["easy", "medium", "hard"]
    
    questions = []
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\lr_questions.csv"
    
    # Initialize CSV if not exists or start fresh
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    print(f"Starting LR data generation using llama-3.1-8b-instant to {output_path}")
    
    for category in categories:
        for i in range(2): # 2 batches of 10
            difficulty = difficulties[(i + (len(questions)//10)) % 3]
            print(f"Generating 10 {difficulty} questions for {category}...")
            prompt = f"""
            Generate 10 different {difficulty} level {category} Logical Reasoning MCQ questions.
            Format STRICTLY as a JSON array of objects:
            [
              {{
                "type": "lr",
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
                # Using a smaller model to avoid daily token limits
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
                                'difficulty': q.get('difficulty', difficulty),
                                'explanation': q.get('explanation', '')
                            })
                    questions.extend(batch)
                    print(f"Added {len(batch)} questions. Total: {len(questions)}")
                else:
                    print(f"Failed to parse batch for {category}")
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(2) # Throttle
            
    print(f"Done. Generated {len(questions)} questions.")

if __name__ == "__main__":
    generate_lr_questions()
