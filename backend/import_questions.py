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
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT,
            option_d TEXT,
            option_e TEXT,
            option_f TEXT,
            option_g TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (test_bank_id) REFERENCES test_banks(id)
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
        options = []
        for letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            option_key = f"option_{letter.lower()}"
            options.append(q.get(option_key))  # None if missing

        # Ensure exactly 7 options
        while len(options) < 7:
            options.append(None)

        row = (
            bank_id,
            q["question"],
            options[0], options[1], options[2], options[3], options[4], options[5], options[6],  # option_a to g
            q["correct_answer"],
            q.get("explanation")
        )

        logging.info(f"Importing question {i} (#{q['question_number']}): {row}")
        try:
            cursor.execute("""
                INSERT INTO questions 
                (test_bank_id, question, option_a, option_b, option_c, option_d, option_e, option_f, option_g, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        except sqlite3.Error as e:
            logging.error(f"Failed on question {i} (#{q['question_number']}): {e}")
            logging.error(f"Problematic row: {row}")
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