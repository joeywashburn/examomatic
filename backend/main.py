from fastapi import FastAPI, HTTPException, Query, UploadFile
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import random
import json
import csv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            exam_code TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_bank_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (test_bank_id) REFERENCES test_banks(id)
        )
    """)

    cursor.execute("SELECT id FROM test_banks WHERE name = ?", ("Default Exam",))
    test_bank = cursor.fetchone()

    if not test_bank:
        cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", 
                      ("Default Exam", "DEMO-001"))
        test_bank_id = cursor.lastrowid  

        sample_questions = [
            {
                "question": "What is 2 + 2?",
                "option_a": "3",
                "option_b": "4",
                "option_c": "5",
                "option_d": "6",
                "correct_answer": "B",
                "explanation": "In basic arithmetic, 2 + 2 equals 4. This is a fundamental mathematical fact that forms the basis of addition. The number 4 (option B) represents the sum of adding two and two together."
            },
            {
                "question": "What color is the sky on a clear day?",
                "option_a": "Red",
                "option_b": "Green",
                "option_c": "Blue",
                "option_d": "Yellow",
                "correct_answer": "C",
                "explanation": "The sky appears blue on a clear day due to a phenomenon called Rayleigh scattering. When sunlight travels through the Earth's atmosphere, it collides with gas molecules. These molecules scatter the light in all directions, but they scatter blue light more strongly than other colors because blue light travels in shorter, smaller waves. This is why we see a blue sky during the day."
            }
        ]

        for q in sample_questions:
            cursor.execute("""
                INSERT INTO questions 
                (test_bank_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_bank_id,
                q["question"],
                q["option_a"],
                q["option_b"],
                q["option_c"],
                q["option_d"],
                q["correct_answer"],
                q["explanation"]
            ))

    conn.commit()
    conn.close()

init_db()

class Question(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: Optional[str]

class Answer(BaseModel):
    question_id: int
    selected_answer: str

def validate_question_shuffle(original_options, shuffled_options, original_correct, new_correct):
    """Validate that answer shuffling was done correctly"""
    # Get the correct answer text from both original and shuffled
    original_correct_text = original_options[ord(original_correct) - ord('A')]
    new_correct_text = shuffled_options[ord(new_correct) - ord('A')]
    
    # Verify the correct answer text matches
    if original_correct_text != new_correct_text:
        raise ValueError(f"Answer validation failed! Original correct answer '{original_correct_text}' does not match new correct answer '{new_correct_text}'")
    
    # Verify all options are present
    if set(original_options) != set(shuffled_options):
        raise ValueError("Answer validation failed! Not all options are present after shuffling")
    
    return True

@app.get("/test_banks")
def get_test_banks():
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tb.id, tb.name, tb.exam_code, COUNT(q.id) as question_count 
        FROM test_banks tb 
        LEFT JOIN questions q ON tb.id = q.test_bank_id 
        GROUP BY tb.id, tb.name, tb.exam_code
    """)
    
    banks = cursor.fetchall()
    result = [{"id": id, "name": name, "exam_code": exam_code, "question_count": count} for id, name, exam_code, count in banks]
    
    conn.close()
    return {"test_banks": result}

@app.post("/test_banks")
def add_test_bank(name: str, exam_code: str):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (name, exam_code))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Test bank already exists.")
    conn.close()
    return {"message": "Test bank added."}

@app.get("/questions")
def get_questions(test_bank_id: int, shuffle: bool = Query(False)):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM test_banks WHERE id = ?", (test_bank_id,))
    bank_id = cursor.fetchone()
    if not bank_id:
        conn.close()
        raise HTTPException(status_code=404, detail="Test bank not found.")
    bank_id = bank_id[0]

    cursor.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation 
        FROM questions WHERE test_bank_id = ?
    """, (bank_id,))
    questions = cursor.fetchall()

    conn.close()

    questions_list = [
        {
            "id": q[0],
            "question": q[1],
            "options": {"A": q[2], "B": q[3], "C": q[4], "D": q[5]},
            "correct_answer": q[6],
            "explanation": q[7] if len(q) > 7 else None
        }
        for q in questions
    ]

    if shuffle:
        random.shuffle(questions_list)

    return {"questions": questions_list}

@app.post("/questions")
def add_question(test_bank: str, question: Question):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM test_banks WHERE name = ?", (test_bank,))
    bank_id = cursor.fetchone()
    if not bank_id:
        conn.close()
        raise HTTPException(status_code=404, detail="Test bank not found.")
    bank_id = bank_id[0]
    
    cursor.execute("""
        INSERT INTO questions (test_bank_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (bank_id, question.question, question.option_a, question.option_b, 
          question.option_c, question.option_d, question.correct_answer, question.explanation))
    
    conn.commit()
    conn.close()
    return {"message": "Question added."}

@app.post("/answer")
def check_answer(answer: Answer):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (answer.question_id,))
    correct = cursor.fetchone()
    if not correct:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found.")
    
    correct_answer = correct[0]
    explanation = correct[1]
    is_correct = answer.selected_answer.upper() == correct_answer.upper()
    conn.close()
    return {"correct": is_correct, "correct_answer": correct_answer, "explanation": explanation}

@app.post("/reset_progress")
def reset_progress():
    return {"message": "Progress reset."}

@app.post("/import")
async def import_questions(file: UploadFile):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    try:
        content = await file.read()
        if file.filename.endswith('.json'):
            data = json.loads(content)
            exam_name = data.get('exam_name')
            exam_code = data.get('exam_code')
            questions = data.get('questions', [])
            
            if not exam_name or not exam_code or not questions:
                raise HTTPException(status_code=400, detail="Invalid JSON format. Must include exam_name, exam_code, and questions.")
            
            cursor.execute("SELECT id FROM test_banks WHERE name = ? OR exam_code = ?", (exam_name, exam_code))
            bank = cursor.fetchone()
            if not bank:
                print(f"Creating new test bank: {exam_name} ({exam_code})")
                cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (exam_name, exam_code))
                bank_id = cursor.lastrowid
            else:
                bank_id = bank[0]
                
            for q in questions:
                cursor.execute("""
                    INSERT INTO questions 
                    (test_bank_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bank_id,
                    q["question"],
                    q["option_a"],
                    q["option_b"],
                    q["option_c"],
                    q["option_d"],
                    q["correct_answer"],
                    q.get("explanation")
                ))
        elif file.filename.endswith(".csv"):
            reader = csv.DictReader(content.decode('utf-8').splitlines())
            questions = list(reader)
            if not questions:
                raise HTTPException(status_code=400, detail="No questions found in CSV file")
            exam_code = questions[0].get("exam_code", "")
            exam_name = questions[0].get("exam_name", "Default Exam")
            print(f"Parsed CSV, found {len(questions)} questions for exam {exam_name} ({exam_code})")
            
            cursor.execute("SELECT id FROM test_banks WHERE name = ?", (exam_name,))
            bank = cursor.fetchone()
            if not bank:
                print(f"Creating new test bank: {exam_name}")
                cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (exam_name, exam_code))
                bank_id = cursor.lastrowid
            else:
                bank_id = bank[0]
            
            for q in questions:
                q_dict = {
                    "question": q["question"],
                    "option_a": q["option_a"],
                    "option_b": q["option_b"],
                    "option_c": q["option_c"],
                    "option_d": q["option_d"],
                    "correct_answer": q["correct_answer"],
                    "explanation": q.get("explanation")
                }
                cursor.execute("""
                    INSERT INTO questions (test_bank_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (bank_id, q_dict["question"], q_dict["option_a"], q_dict["option_b"], 
                      q_dict["option_c"], q_dict["option_d"], q_dict["correct_answer"], q_dict["explanation"]))
        
        conn.commit()
        conn.close()
        return {"message": f"Successfully imported questions into {exam_name} ({exam_code})"}
    except Exception as e:
        conn.close()
        print(f"Import failed with error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
