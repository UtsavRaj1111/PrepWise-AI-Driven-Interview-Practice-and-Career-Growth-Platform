import os
import csv
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extensions import supabase as handler

def load_csv(file_path, q_type):
    questions = []
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return []
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                options = json.loads(row['options'])
            except:
                options = row['options']
                
            questions.append({
                "type": q_type,
                "category": row['category'],
                "question": row['question'],
                "options": options,
                "answer": row['answer'],
                "difficulty": row['difficulty'].lower(),
                "explanation": row['explanation']
            })
    return questions

def migrate_tenses():
    if not handler.client:
        print("Error: Supabase client not initialized. Check your .env file.")
        return

    tenses_file = r"c:\Users\Utsav Raj\OneDrive\Desktop\Prep\data_tools\tenses_questions.csv"
    print(f"Loading Tenses questions from {tenses_file}...")
    tenses_questions = load_csv(tenses_file, 'va')
    
    print(f"Total Tenses questions to upload: {len(tenses_questions)}")
    
    if tenses_questions:
        res = handler.batch_insert_questions(tenses_questions)
        if res:
            print(f"Successfully uploaded {len(res)} Tenses questions to Supabase!")
        else:
            print("Failed to upload questions.")
    else:
        print("No questions found to upload.")

if __name__ == "__main__":
    migrate_tenses()
