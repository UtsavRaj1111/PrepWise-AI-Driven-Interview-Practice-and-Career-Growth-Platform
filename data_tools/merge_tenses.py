import csv
import os

def append_tenses_to_va():
    tenses_file = r"c:\Users\Utsav Raj\OneDrive\Desktop\Prep\data_tools\tenses_questions.csv"
    va_file = r"c:\Users\Utsav Raj\OneDrive\Desktop\Prep\data_tools\va_questions.csv"
    
    if not os.path.exists(tenses_file):
        print(f"Error: {tenses_file} not found.")
        return
    
    with open(tenses_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        questions = list(reader)
        
    print(f"Read {len(questions)} questions from {tenses_file}")
    
    file_exists = os.path.exists(va_file)
    
    with open(va_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['type', 'category', 'question', 'options', 'answer', 'difficulty', 'explanation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        for q in questions:
            writer.writerow(q)
            
    print(f"Successfully appended {len(questions)} questions to {va_file}")

if __name__ == "__main__":
    append_tenses_to_va()
