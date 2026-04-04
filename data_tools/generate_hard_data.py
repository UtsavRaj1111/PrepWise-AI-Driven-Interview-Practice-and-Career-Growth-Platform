import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_hard_questions():
    ai = AIHandler()
    categories = [
        "Profit and Loss", "Time and Work", "Time and Distance", "Percentages",
        "Ratio and Proportion", "Number System", "Probability", "Interest",
        "Averages", "Permutations and Combinations"
    ]
    
    questions = []
    
    for category in categories:
        print(f"Generating HARD questions for category: {category}")
        # 1 batch of 10 hard questions per category
        prompt = f"""
        Generate 10 different HARD level {category} MCQ aptitude questions.
        These should be challenging, multi-step problems suitable for advanced competitive exams.
        Format STRICTLY as a JSON array of objects:
        [
          {{
            "type": "aptitude",
            "category": "{category.lower().replace(' ', '_')}",
            "question": "...",
            "options": ["...", "...", "...", "..."],
            "answer": "<one of the options exactly>",
            "difficulty": "hard",
            "explanation": "..."
          }}
        ]
        No extra text, no markdown, just the JSON array.
        """
        try:
            response = ai.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            batch = json.loads(content)
            
            if isinstance(batch, dict) and "questions" in batch:
                batch = batch["questions"]
            elif isinstance(batch, dict) and len(batch) == 1:
                batch = list(batch.values())[0]
            
            if isinstance(batch, list):
                questions.extend(batch)
            else:
                print(f"Warning: Batch for {category} was not a list.")
        except Exception as e:
            print(f"Error generating batch for {category}: {e}")
        
        time.sleep(1)
            
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\hard_aptitude_questions.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for q in questions[:100]:
            if isinstance(q.get('options'), list):
                q['options'] = json.dumps(q['options'])
            writer.writerow({
                'type': q.get('type', 'aptitude'),
                'category': q.get('category', 'general'),
                'question': q.get('question', ''),
                'options': q.get('options', '[]'),
                'answer': q.get('answer', ''),
                'difficulty': 'hard',
                'explanation': q.get('explanation', '')
            })
    
    print(f"Successfully generated {len(questions)} hard questions to {output_path}")

if __name__ == "__main__":
    generate_hard_questions()
