import sqlite3
import json
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_db(db_path):
    """Initialize the database if it doesn’t exist."""
    conn = sqlite3.connect(db_path)
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

    conn.commit()
    conn.close()
    logging.info(f"Database initialized at {db_path}")

def import_json(file_path, db_path):
    """Import questions from a JSON file into the database."""
    # Load JSON
    with open(file_path, 'r') as f:
        data = json.load(f)

    exam_name = data.get('exam_name')
    exam_code = data.get('exam_code')
    questions = data.get('questions', [])

    if not exam_name or not exam_code or not questions:
        logging.error("Invalid JSON format. Must include exam_name, exam_code, and questions.")
        return

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check or create test bank
    cursor.execute("SELECT id FROM test_banks WHERE name = ? OR exam_code = ?", (exam_name, exam_code))
    bank = cursor.fetchone()
    if not bank:
        logging.info(f"Creating new test bank: {exam_name} ({exam_code})")
        cursor.execute("INSERT INTO test_banks (name, exam_code) VALUES (?, ?)", (exam_name, exam_code))
        bank_id = cursor.lastrowid
    else:
        bank_id = bank[0]
        logging.info(f"Using existing test bank ID {bank_id} for {exam_name}")

    # Import questions
    for i, q in enumerate(questions, 1):
        try:
            # Validate and prepare correct_answer
            correct_answer = q.get("correct_answer")
            if correct_answer is None:
                raise ValueError("'correct_answer' is null or missing")
            if isinstance(correct_answer, list):
                correct_answer = ",".join(str(x) for x in correct_answer)
            if not correct_answer:
                raise ValueError("'correct_answer' is empty")

            explanation = q.get("explanation")
            if isinstance(explanation, list):
                explanation = " ".join(str(e) for e in explanation) if explanation else None

            # Insert into questions table
            cursor.execute("""
                INSERT INTO questions (test_bank_id, question, correct_answer, explanation)
                VALUES (?, ?, ?, ?)
            """, (bank_id, q["question"], correct_answer, explanation))
            question_id = cursor.lastrowid

            # Collect and insert options
            options = []
            for letter in 'ABCDEFGHIJ':
                option_key = f"option_{letter.lower()}"
                if option_key in q and q[option_key] is not None:
                    options.append((letter, q[option_key]))

            if not options:
                raise ValueError("No valid options provided")

            for option_letter, option_text in options:
                cursor.execute("""
                    INSERT INTO question_options (question_id, option_letter, option_text)
                    VALUES (?, ?, ?)
                """, (question_id, option_letter, option_text))

            logging.info(f"Imported question {i} (#{q.get('question_number', 'N/A')}): {q['question']}")

        except Exception as e:
            logging.error(f"Failed on question {i} (#{q.get('question_number', 'N/A')}): {str(e)}")
            logging.error(f"Problematic data: {json.dumps(q)}")
            conn.rollback()
            conn.close()
            return

    conn.commit()
    conn.close()
    logging.info(f"Successfully imported {len(questions)} questions into {exam_name} ({exam_code})")

def main():
    parser = argparse.ArgumentParser(description="Import JSON exam questions into SQLite database.")
    parser.add_argument("json_file", help="Path to the JSON file to import")
    parser.add_argument("--db", default="test_engine.db", help="Path to SQLite database file (default: test_engine.db)")
    args = parser.parse_args()

    init_db(args.db)
    import_json(args.json_file, args.db)

if __name__ == "__main__":
    main()