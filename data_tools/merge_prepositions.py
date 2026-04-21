import csv
import os

def merge_csv():
    base_dir = os.path.dirname(__file__)
    main_va_path = os.path.join(base_dir, 'va_questions.csv')
    new_prep_path = os.path.join(base_dir, 'prepositions_questions.csv')
    
    if not os.path.exists(new_prep_path):
        print("New prepositions file not found.")
        return
        
    # Read new questions
    with open(new_prep_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        new_questions = list(reader)
        
    print(f"Read {len(new_questions)} new questions.")
    
    # Append to main VA file
    file_exists = os.path.exists(main_va_path)
    with open(main_va_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_questions[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_questions)
        
    print(f"Successfully appended {len(new_questions)} questions to {main_va_path}")

if __name__ == "__main__":
    merge_csv()
