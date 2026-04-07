import os
import csv
import json
import time
from ai_handler import AIHandler

def generate_questions():
    ai = AIHandler()
    categories = [
        "Profit and Loss", "Time and Work", "Time and Distance", "Percentages",
        "Ratio and Proportion", "Number System", "Probability", "Interest",
        "Averages", "Logic"
    ]
    difficulties = ["easy", "medium", "hard"]
    
    questions = []
    
    # We want 200 questions, so 20 per category.
    # To speed up, we'll ask for 10 at a time in a custom prompt.
    
    for category in categories:
        print(f"Generating for category: {category}")
        for i in range(2): # 2 batches of 10
            difficulty = difficulties[i % 3]
            prompt = f"""
            Generate 10 different {difficulty} level {category} MCQ aptitude questions.
            Format STRICTLY as a JSON array of objects:
            [
              {{
                "type": "aptitude",
                "category": "{category.lower().replace(' ', '_')}",
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": "<one of the options exactly>",
                "difficulty": "{difficulty}",
                "explanation": "..."
              }},
              ...
            ]
            No extra text, no markdown, just the JSON array.
            """
            try:
                # Use a custom call to Groq via AIHandler's client
                response = ai.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                batch = json.loads(response.choices[0].message.content)
                # Some LLMs might return a wrapper object like {"questions": [...]}
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
            
            time.sleep(1) # Rate limit respect
            
    # Save to CSV
    # Re-verify and deduplicate if necessary (though seed/index help)
    output_path = "c:\\Users\\Utsav Raj\\OneDrive\\Desktop\\Prep\\aptitude_questions.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for q in questions[:200]: # Cap at 200
            # Ensure options are JSON string as requested
            if isinstance(q.get('options'), list):
                q['options'] = json.dumps(q['options'])
            writer.writerow({
                'type': q.get('type', 'aptitude'),
                'category': q.get('category', 'general'),
                'question': q.get('question', ''),
                'options': q.get('options', '[]'),
                'answer': q.get('answer', ''),
                'difficulty': q.get('difficulty', 'medium'),
                'explanation': q.get('explanation', '')
            })
    
    print(f"Successfully generated {len(questions)} questions to {output_path}")

if __name__ == "__main__":
    generate_questions()
