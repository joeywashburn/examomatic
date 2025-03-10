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
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (test_bank_id) REFERENCES test_banks(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            option_letter TEXT NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_bank_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_bank_id) REFERENCES test_banks(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

class Question(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: Optional[str]
    option_d: Optional[str]
    option_e: Optional[str]
    option_f: Optional[str]
    option_g: Optional[str]
    correct_answer: str
    explanation: Optional[str]

class Answer(BaseModel):
    question_id: int
    selected_answer: str

def validate_question_shuffle(original_options, shuffled_options, original_correct, new_correct):
    original_correct_text = original_options[ord(original_correct) - ord('A')]
    new_correct_text = shuffled_options[ord(new_correct) - ord('A')]
    if original_correct_text != new_correct_text:
        raise ValueError(f"Answer validation failed! Original correct answer '{original_correct_text}' does not match new correct answer '{new_correct_text}'")
    if set(original_options) != set(shuffled_options):
        raise ValueError("Answer validation failed! Not all options are present after shuffling")
    return True

@app.get("/test_banks")
def get_test_banks():
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    
    # Fetch test banks with their question count
    cursor.execute("""
        SELECT tb.id, tb.name, tb.exam_code, COUNT(q.id) as question_count 
        FROM test_banks tb 
        LEFT JOIN questions q ON tb.id = q.test_bank_id 
        GROUP BY tb.id, tb.name, tb.exam_code
    """)
    banks = cursor.fetchall()
    
    result = []
    for id, name, exam_code, count in banks:
        # Fetch the most recent exam result for this test bank
        cursor.execute("""
            SELECT score, total_questions 
            FROM exam_results 
            WHERE test_bank_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (id,))
        last_result = cursor.fetchone()
        
        # Calculate the last score (percentage) if a result exists
        last_score = None
        if last_result:
            score, total_questions = last_result
            last_score = (score / total_questions * 100) if total_questions > 0 else 0
        
        # Add the test bank to the result with the last_score
        result.append({
            "id": id,
            "name": name,
            "exam_code": exam_code,
            "question_count": count,
            "last_score": last_score  # Add the last_score field (can be null if no results exist)
        })
    
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
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Test bank not found.")
    cursor.execute("SELECT id, question, correct_answer, explanation FROM questions WHERE test_bank_id = ?", (test_bank_id,))
    questions = cursor.fetchall()
    print("Fetched questions:", questions)
    questions_list = []
    for q_id, question, correct_answer, explanation in questions:
        cursor.execute("SELECT option_letter, option_text FROM question_options WHERE question_id = ? ORDER BY option_letter", (q_id,))
        options = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"Options for question {q_id}: {options}")
        questions_list.append({
            "id": q_id,
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        })
    if shuffle:
        random.shuffle(questions_list)
        for q in questions_list:
            opts = list(q["options"].items())
            random.shuffle(opts)
            q["options"] = dict(opts)
            if ',' in q["correct_answer"]:
                old_answers = q["correct_answer"].split(',')
                new_answers = []
                for old_ans in old_answers:
                    for new_letter, text in opts:
                        if text == q["options"][old_ans]:
                            new_answers.append(new_letter)
                            break
                q["correct_answer"] = ",".join(sorted(new_answers))
    print("Returning questions_list:", questions_list)
    conn.close()
    return {"questions": questions_list}

@app.post("/answer")
def check_answer(answer: Answer):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (answer.question_id,))
    correct = cursor.fetchone()
    if not correct:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found.")
    correct_answers = set(correct[0].split(','))
    selected = answer.selected_answer.upper()
    is_correct = selected in correct_answers
    conn.close()
    return {"correct": is_correct, "correct_answer": correct[0], "explanation": correct[1]}

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
                raise HTTPException(status_code=400, detail="Invalid JSON format: 'exam_name', 'exam_code', or 'questions' missing.")

            # Check if test bank exists, create it if not
            cursor.execute("SELECT id FROM test_banks WHERE name = ? OR exam_code = ?", (exam_name, exam_code))
            bank = cursor.fetchone()
            if not bank:
                cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (exam_name, exam_code))
                bank_id = cursor.lastrowid
            else:
                bank_id = bank[0]

            # Process each question with detailed error reporting
            for index, q in enumerate(questions, start=1):  # Start counting at 1 for readability
                try:
                    # Validate correct_answer before insertion
                    correct_answer = q.get("correct_answer")
                    if correct_answer is None:
                        raise ValueError(f"'correct_answer' is null or missing in question at position {index}")
                    if isinstance(correct_answer, list):
                        correct_answer = ",".join(str(x) for x in correct_answer)
                    if not correct_answer:  # Check if it's an empty string after processing
                        raise ValueError(f"'correct_answer' is empty in question at position {index}")

                    explanation = q.get("explanation")
                    if isinstance(explanation, list):
                        explanation = " ".join(str(e) for e in explanation) if explanation else None

                    # Insert question into the database
                    cursor.execute("""
                        INSERT INTO questions (test_bank_id, question, correct_answer, explanation)
                        VALUES (?, ?, ?, ?)
                    """, (bank_id, q["question"], correct_answer, explanation))
                    question_id = cursor.lastrowid

                    # Insert options
                    options = []
                    for letter in 'ABCDEFGHIJKLM':
                        option_key = f"option_{letter.lower()}"
                        if option_key in q and q[option_key] is not None:
                            options.append((letter, q[option_key]))
                    for option_letter, option_text in options:
                        cursor.execute("""
                            INSERT INTO question_options (question_id, option_letter, option_text)
                            VALUES (?, ?, ?)
                        """, (question_id, option_letter, option_text))

                except Exception as e:
                    conn.rollback()  # Roll back any changes if an error occurs
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to process question at position {index}: {str(e)}. Problematic data: {json.dumps(q)}"
                    )

            conn.commit()
            conn.close()
            return {"message": f"Successfully imported questions into {exam_name} ({exam_code})"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JSON file.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@app.delete("/test_banks/{test_bank_id}")
def delete_test_bank(test_bank_id: int):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM questions WHERE test_bank_id = ?", (test_bank_id,))
        cursor.execute("DELETE FROM test_banks WHERE id = ?", (test_bank_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Test bank not found")
        conn.commit()
        return {"message": "Test bank and associated questions deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/exam_results")
def save_exam_result(test_bank_id: int, score: int, total_questions: int):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO exam_results (test_bank_id, score, total_questions) VALUES (?, ?, ?)",
            (test_bank_id, score, total_questions)
        )
        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        return {"id": result_id, "message": "Result saved successfully"}
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exam_results/{test_bank_id}")
def get_exam_results(test_bank_id: int):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT score, total_questions, timestamp 
        FROM exam_results 
        WHERE test_bank_id = ? 
        ORDER BY timestamp DESC
        LIMIT 10
    """, (test_bank_id,))
    results = cursor.fetchall()
    conn.close()
    return {
        "results": [
            {
                "score": r[0],
                "total_questions": r[1],
                "timestamp": r[2].isoformat(),
                "percentage": (r[0] / r[1] * 100) if r[1] > 0 else 0
            }
            for r in results
        ]
    }

@app.get("/exam_history/{test_bank_id}")
def get_exam_history(test_bank_id: int):
    conn = sqlite3.connect("test_engine.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT score, total_questions, timestamp 
        FROM exam_results 
        WHERE test_bank_id = ? 
        ORDER BY timestamp DESC
    """, (test_bank_id,))
    results = cursor.fetchall()
    conn.close()
    return {
        "history": [
            {
                "score": r[0],
                "total_questions": r[1],
                "timestamp": r[2].isoformat(),
                "percentage": (r[0] / r[1] * 100) if r[1] > 0 else 0
            }
            for r in results
        ]
    }