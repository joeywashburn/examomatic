from fastapi import FastAPI, HTTPException, Query, UploadFile
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import json
import random
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Create exams directory if it doesn't exist
os.makedirs("exams", exist_ok=True)

# Mount the exams directory to serve static files (images)
app.mount("/exams", StaticFiles(directory="exams"), name="exams")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Delete the existing database to reset with the new schema
SQLITE_DB = "test_engine.db"
if os.path.exists(SQLITE_DB):
    os.remove(SQLITE_DB)

def init_db():
    conn = sqlite3.connect(SQLITE_DB)
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
            question_text TEXT NOT NULL,
            explanation TEXT,
            question_images TEXT,  -- Store as JSON string, e.g., '["image1.png", "image2.png"]'
            explanation_images TEXT,  -- Fixed typo: was 'explanation crabs'
            FOREIGN KEY (test_bank_id) REFERENCES test_banks(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            option_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            image TEXT,  -- New field for option image
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

class ExamResultRequest(BaseModel):
    test_bank_id: int
    score: int
    total_questions: int
    
class Question(BaseModel):
    question_text: str
    options: List[dict]
    explanation: Optional[str]
    question_images: Optional[List[str]]
    explanation_images: Optional[List[str]]

class Answer(BaseModel):
    question_id: int
    selected_answer: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Exam API. Visit /docs for API documentation."}

@app.get("/test_banks")
def get_test_banks():
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tb.id, tb.name, tb.exam_code, COUNT(q.id) as question_count 
        FROM test_banks tb 
        LEFT JOIN questions q ON tb.id = q.test_bank_id 
        GROUP BY tb.id, tb.name, tb.exam_code
    """)
    banks = cursor.fetchall()
    
    result = []
    for id, name, exam_code, count in banks:
        cursor.execute("""
            SELECT score, total_questions 
            FROM exam_results 
            WHERE test_bank_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 3
        """, (id,))
        last_results = cursor.fetchall()
        
        last_three_scores = [
            (score / total_questions * 100) if total_questions > 0 else 0
            for score, total_questions in last_results
        ]
        while len(last_three_scores) < 3:
            last_three_scores.append(None)
        
        result.append({
            "id": id,
            "name": name,
            "exam_code": exam_code,
            "question_count": count,
            "last_three_scores": last_three_scores
        })
    
    conn.close()
    return {"test_banks": result}

@app.post("/test_banks")
def add_test_bank(name: str, exam_code: str):
    conn = sqlite3.connect(SQLITE_DB)
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
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, exam_code FROM test_banks WHERE id = ?", (test_bank_id,))
        test_bank = cursor.fetchone()
        if not test_bank:
            conn.close()
            raise HTTPException(status_code=404, detail="Test bank not found.")
        exam_code = test_bank[1]
        
        cursor.execute("SELECT id, question_text, explanation, question_images, explanation_images FROM questions WHERE test_bank_id = ?", (test_bank_id,))
        questions = cursor.fetchall()
        
        questions_list = []
        for q_id, question_text, explanation, question_images, explanation_images in questions:
            cursor.execute("SELECT id, option_text, is_correct, image FROM options WHERE question_id = ? ORDER BY id", (q_id,))
            options = cursor.fetchall()
            if not options:
                continue
            
            fixed_letters = [chr(97 + i) for i in range(len(options))]
            option_dict = {fixed_letters[i]: text for i, (opt_id, text, _, _) in enumerate(options)}
            option_images = {fixed_letters[i]: image for i, (opt_id, _, _, image) in enumerate(options)}
            is_correct_list = [bool(is_correct) for _, _, is_correct, _ in options]
            
            if shuffle:
                indices = list(range(len(options)))
                random.shuffle(indices)
                shuffled_options = {fixed_letters[i]: options[indices[i]][1] for i in range(len(options))}
                shuffled_option_images = {fixed_letters[i]: options[indices[i]][3] for i in range(len(options))}
                shuffled_is_correct = [is_correct_list[indices[i]] for i in range(len(options))]
            else:
                shuffled_options = option_dict
                shuffled_option_images = option_images
                shuffled_is_correct = is_correct_list
            
            correct_answers = [fixed_letters[i] for i, is_correct in enumerate(shuffled_is_correct) if is_correct]
            correct_answer = ",".join(correct_answers) if correct_answers else ""
            
            # Parse question_images and construct URLs
            question_images_list = json.loads(question_images) if question_images else []
            question_images_urls = [f"/exams/{exam_code}/images/{img}" if img else None for img in question_images_list]
            
            # Parse explanation_images and construct URLs
            explanation_images_list = json.loads(explanation_images) if explanation_images else []
            explanation_images_urls = [f"/exams/{exam_code}/images/{img}" if img else None for img in explanation_images_list]
            
            # Construct option image URLs
            option_images_urls = {key: f"/exams/{exam_code}/images/{img}" if img else None for key, img in shuffled_option_images.items()}
            
            questions_list.append({
                "id": q_id,
                "question": question_text,
                "options": shuffled_options,
                "option_images": option_images_urls,
                "correct_answer": correct_answer,
                "explanation": explanation or "",
                "question_images": question_images_urls,
                "explanation_images": explanation_images_urls
            })
        
        conn.close()
        return {"questions": questions_list}
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/answer")
def check_answer(answer: Answer):
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, test_bank_id, explanation, explanation_images FROM questions WHERE id = ?", (answer.question_id,))
    question = cursor.fetchone()
    if not question:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found.")
    
    question_id, test_bank_id, explanation, explanation_images = question
    
    cursor.execute("SELECT id, is_correct FROM options WHERE question_id = ? ORDER BY id", (answer.question_id,))
    options = cursor.fetchall()
    fixed_letters = [chr(97 + i) for i in range(len(options))]
    correct_indices = [fixed_letters[i] for i, (opt_id, is_correct) in enumerate(options) if is_correct]
    correct_answer = ",".join(correct_indices) if correct_indices else ""
    
    cursor.execute("SELECT exam_code FROM test_banks WHERE id = ?", (test_bank_id,))
    exam_code = cursor.fetchone()[0]
    explanation_images_list = json.loads(explanation_images) if explanation_images else []
    explanation_images_urls = [f"/exams/{exam_code}/images/{img}" if img else None for img in explanation_images_list]
    
    correct_answers = set(correct_answer.split(','))
    selected = answer.selected_answer.lower()
    is_correct = selected in correct_answers
    
    conn.close()
    return {
        "correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation or "",
        "explanation_images": explanation_images_urls
    }

@app.post("/import")
async def import_questions(file: UploadFile):
    conn = sqlite3.connect(SQLITE_DB)
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

            cursor.execute("SELECT id FROM test_banks WHERE name = ? OR exam_code = ?", (exam_name, exam_code))
            bank = cursor.fetchone()
            if not bank:
                cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (exam_name, exam_code))
                bank_id = cursor.lastrowid
            else:
                bank_id = bank[0]

            exam_image_dir = f"exams/{exam_code}/images"
            os.makedirs(exam_image_dir, exist_ok=True)

            for index, q in enumerate(questions, start=1):
                try:
                    question_text = q.get("question")
                    explanation = q.get("explanation")
                    question_images = q.get("question_images")
                    explanation_images = q.get("explanation_images")
                    if not question_text:
                        raise ValueError(f"'question' is empty or missing in question at position {index}")

                    # Convert lists to JSON strings for storage
                    question_images_json = json.dumps(question_images) if question_images else None
                    explanation_images_json = json.dumps(explanation_images) if explanation_images else None

                    cursor.execute("""
                        INSERT INTO questions (test_bank_id, question_text, explanation, question_images, explanation_images)
                        VALUES (?, ?, ?, ?, ?)
                    """, (bank_id, question_text, explanation, question_images_json, explanation_images_json))
                    question_id = cursor.lastrowid

                    options = q.get("options", [])
                    for opt in options:
                        option_text = opt.get("text")
                        is_correct = bool(opt.get("is_correct", False))
                        option_image = opt.get("image")
                        if option_text:
                            cursor.execute("""
                                INSERT INTO options (question_id, option_text, is_correct, image)
                                VALUES (?, ?, ?, ?)
                            """, (question_id, option_text, is_correct, option_image))

                except Exception as e:
                    conn.rollback()
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
    conn = sqlite3.connect(SQLITE_DB)
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
def save_exam_result(request: ExamResultRequest):
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO exam_results (test_bank_id, score, total_questions) VALUES (?, ?, ?)",
            (request.test_bank_id, request.score, request.total_questions)
        )

        cursor.execute(
            "SELECT COUNT(*) FROM exam_results WHERE test_bank_id = ?",
            (request.test_bank_id,)
        )
        result_count = cursor.fetchone()[0]

        if result_count > 3:
            to_delete = result_count - 3
            cursor.execute(
                """
                DELETE FROM exam_results
                WHERE id IN (
                    SELECT id FROM exam_results
                    WHERE test_bank_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
                """,
                (request.test_bank_id, to_delete)
            )

        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        return {"id": result_id, "message": "Result saved successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exam_results/{test_bank_id}")
def get_exam_results(test_bank_id: int):
    conn = sqlite3.connect(SQLITE_DB)
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
                "timestamp": str(r[2]),
                "percentage": (r[0] / r[1] * 100) if r[1] > 0 else 0
            }
            for r in results
        ]
    }

@app.get("/exam_history/{test_bank_id}")
def get_exam_history(test_bank_id: int):
    conn = sqlite3.connect(SQLITE_DB)
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
                "timestamp": str(r[2]),
                "percentage": (r[0] / r[1] * 100) if r[1] > 0 else 0
            }
            for r in results
        ]
    }