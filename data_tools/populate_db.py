import os
import csv
import json
from supabase_handler import SupabaseHandler

def load_csv(file_path, q_type):
    questions = []
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return []
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse options if it's a string representation of a list
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

def migrate():
    handler = SupabaseHandler()
    if not handler.client:
        print("Error: Supabase client not initialized. Check your .env file.")
        return

    all_questions = []
    
    # 1. Aptitude (Normal + Hard)
    print("Loading Aptitude questions...")
    all_questions.extend(load_csv('aptitude_questions.csv', 'aptitude'))
    all_questions.extend(load_csv('hard_aptitude_questions.csv', 'aptitude'))
    
    # 2. Logical Reasoning
    print("Loading Logical Reasoning questions...")
    all_questions.extend(load_csv('lr_questions.csv', 'lr'))
    
    # 3. Verbal Ability
    print("Loading Verbal Ability questions...")
    all_questions.extend(load_csv('va_questions.csv', 'va'))
    
    print(f"Total questions to upload: {len(all_questions)}")
    
    if all_questions:
        res = handler.batch_insert_questions(all_questions)
        if res:
            print(f"Successfully uploaded {len(res)} questions to Supabase!")
        else:
            print("Failed to upload questions.")
    else:
        print("No questions found to upload.")

if __name__ == "__main__":
    migrate()
