import os
import csv
import json
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions import supabase as handler

def load_csv(file_path):
    questions = []
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                options = json.loads(row['options'])
            except:
                options = row['options']
                
            questions.append({
                "type": "va",
                "category": "prepositions",
                "question": row['question'],
                "options": options,
                "answer": row['answer'],
                "difficulty": row['difficulty'].lower(),
                "explanation": row['explanation']
            })
    return questions

def migrate():
    if not handler.client:
        print("Error: Supabase client not initialized.")
        return

    csv_path = os.path.join(os.path.dirname(__file__), 'prepositions_questions.csv')
    print(f"Loading questions from {csv_path}...")
    questions = load_csv(csv_path)
    
    print(f"Total questions to upload: {len(questions)}")
    
    if questions:
        # Use batch_insert_questions which handles chunking
        res = handler.batch_insert_questions(questions)
        if res:
            print(f"Successfully uploaded {len(res)} questions to Supabase!")
        else:
            print("Failed to upload questions.")
    else:
        print("No questions found to upload.")

if __name__ == "__main__":
    migrate()
