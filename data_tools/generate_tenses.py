import os
import csv
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def generate_tenses_questions():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        return

    client = Groq(api_key=api_key)
    model = "llama-3.1-8b-instant"
    
    output_path = r"c:\Users\Utsav Raj\OneDrive\Desktop\Prep\data_tools\tenses_questions.csv"
    
    print(f"Starting Tenses questions generation. Appending to {output_path}")
    
    # Overwrite file for a fresh start with better questions
    if os.path.exists(output_path):
        os.remove(output_path)
    file_exists = False
    
    total_needed = 150
    batch_size = 10
    batches = total_needed // batch_size
    
    questions_count = 0
    
    for i in range(batches):
        difficulty = "easy" if i < 5 else "medium" if i < 10 else "hard"
        print(f"Generating batch {i+1}/{batches} ({difficulty})...")
        
        prompt = f"""
        Generate 10 unique {difficulty} level MCQ Verbal Ability questions specifically on the topic of 'Tenses'.
        
        DIFFICULTY CRITERIA:
        - Easy: Simple Present, Past, and Future. Basic sentence structures.
        - Medium: Present Perfect, Past Perfect, Future Perfect, and Continuous variations. Mixed time references and common irregular verbs.
        - Hard: Mixed Conditionals (e.g., If I had known, I would be...), Subjunctive mood, Future Perfect Continuous, Past Perfect Continuous in complex multi-clause sentences, and nuances between similarly used tenses (e.g., Present Perfect vs. Simple Past in specific contexts).
        
        Format STRICTLY as a JSON object with a "questions" key:
        {{
          "questions": [
            {{
              "type": "va",
              "category": "tenses",
              "question": "By the time the sun sets tomorrow, we ___ for over forty-eight hours without a break.",
              "options": ["A. will work", "B. will have been working", "C. would have worked", "D. are working"],
              "answer": "B",
              "difficulty": "{difficulty}",
              "explanation": "The Future Perfect Continuous tense is used to describe an action that will be continuing up until a point in the future."
            }}
          ]
        }}
        No extra text, just JSON. Ensure the options are formatted with A., B., C., D. prefixes.
        """
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            batch_data = json.loads(response.choices[0].message.content)
            
            # Handle different JSON structures AI might return
            if isinstance(batch_data, dict):
                if "questions" in batch_data:
                    batch = batch_data["questions"]
                elif len(batch_data) == 1:
                    batch = list(batch_data.values())[0]
                else:
                    batch = [batch_data]
            else:
                batch = batch_data

            if isinstance(batch, list):
                with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                        file_exists = True
                    
                    for q in batch:
                        # Ensure options is a JSON string
                        options = q.get('options', [])
                        if isinstance(options, list):
                            options_str = json.dumps(options)
                        else:
                            options_str = options
                            
                        writer.writerow({
                            'type': 'va',
                            'category': 'tenses',
                            'question': q.get('question', ''),
                            'options': options_str,
                            'answer': q.get('answer', ''),
                            'difficulty': q.get('difficulty', difficulty),
                            'explanation': q.get('explanation', '')
                        })
                
                questions_count += len(batch)
                print(f"Added {len(batch)} questions. Total: {questions_count}")
            else:
                print(f"Failed to parse batch {i+1}")
                
        except Exception as e:
            print(f"Error in batch {i+1}: {e}")
        
        # Avoid rate limits
        time.sleep(1)

    print(f"Done. Generated {questions_count} questions for Tenses.")

if __name__ == "__main__":
    generate_tenses_questions()
