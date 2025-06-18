# ExamOMatic
A simple exam practice application that allows you to import and practice exam questions.

## Features
Import questions from JSON files
Multiple exam support
Practice mode with immediate feedback
Support for multiple choice questions
Support for questions and options with images

## Prerequisites

- Python 3.8 or higher
- Node.js 18.x or higher
- npm (comes with Node.js)

## Installation

### Clone the repository:

```bash
git clone <repository-url>
cd examomatic
```
### Set up Python environment:

### Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
### Install Python dependencies
```
pip install -r requirements.txt
```
### Set up Frontend:

### Install frontend dependencies

```bash
cd frontend/exam-o-matic
npm install
cd ../..
```

### Running the Application

- Start both services with one command:

```bash
chmod +x run.sh  # Make the script executable (only needed once)
./run.sh
```
The script will start both the backend and frontend servers. If the default ports (4200 for frontend, 8000 for backend) are in use, the script will automatically find and use the next available ports.
The actual URLs will be displayed when the services start.
The script handles:

- Automatic port selection if default ports are in use
- Starting both services in the correct order
- Graceful shutdown of both services when you press Ctrl+C

Press Ctrl+C to stop both services.

## File Format

- JSON Format

Questions can be imported using JSON files.
Here's the required format:
```json
{
  "exam_name": "Mixed Questions Test",
  "exam_code": "MIX-101",
  "questions": [
    {
      "question": "This question has images. Starting image: [image1] Modified to: [image2] Choose the next step.",
      "question_images": ["image1.png", "image2.png"],
      "options": [
        {"text": "Option A", "is_correct": false, "image": "choice_image1.png"},
        {"text": "Option B", "is_correct": true, "image": "choice_image2.png"},
        {"text": "Option C", "is_correct": false, "image": "choice_image3.png"},
        {"text": "Option D", "is_correct": false, "image": "choice_image4.png"}
      ],
      "explanation": "Explanation with images: [explanation_image1] More details: [explanation_image2]",
      "explanation_images": ["explanation_image1.png", "explanation_image2.png"]
    },
    {
      "question": "This question has no images. What is the capital of France?",
      "question_images": [],
      "options": [
        {"text": "Spain", "is_correct": false},
        {"text": "Germany", "is_correct": false},
        {"text": "France", "is_correct": true},
        {"text": "Italy", "is_correct": false}
      ],
      "explanation": "The capital of France is Paris.",
      "explanation_images": []
    }
  ]
}
```
### Required fields:

- exam_name: The display name of the exam
- exam_code: A unique identifier for the exam (e.g., "MIX-101", "CLF-C02")
- questions: An array of question objects, each containing:
- question: The question text
- question_images: Array of image filenames referenced in the question text (empty if none)
- options: Array of option objects, each with:
- text: Option text
- is_correct: Boolean indicating if the option is correct
- image: Optional image filename for the option (omit if none)


- explanation: Explanation of the correct answer
- explanation_images: Array of image filenames referenced in the explanation (empty if none)



#### Multiple Answer Questions
For questions with multiple correct answers, set is_correct to true for each correct option:
```json
{
  "exam_name": "AWS Certified Cloud Practitioner",
  "exam_code": "CLF-C02",
  "questions": [
    {
      "question": "Which of these are AWS compute services? (Select all that apply)",
      "question_images": [],
      "options": [
        {"text": "EC2", "is_correct": true},
        {"text": "Lambda", "is_correct": true},
        {"text": "S3", "is_correct": false},
        {"text": "RDS", "is_correct": false}
      ],
      "explanation": "EC2 and Lambda are AWS compute services.",
      "explanation_images": []
    }
  ]
}
```
- Notes about multiple-answer questions:

-  Multiple options can have "is_correct": true
- In the UI, these questions will show checkboxes instead of radio buttons
- All correct options must be selected to get the question right

### Project Structure


```text
examomatic/
├── backend/           # FastAPI backend
│   └── main.py       # Main backend code
├── data/             # Sample question files
├── frontend/         # Angular frontend
├── requirements.txt  # Python dependencies
└── run.sh           # Script to run both services
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Creating Exam Files with AI
You can leverage AI tools like Claude to help create high-quality exam questions. Here's an effective process:

### Gather Official Exam Objectives

Download the official exam objectives from the vendor's website

These objectives typically include domain weightings (e.g., Domain 1: 20%, Domain 2: 30%, etc.)


### Generate Questions Using AI

Share the exam objectives with an AI assistant (like Claude)

Ask it to analyze the objectives and domain weightings

Request multiple-choice questions that align with the objectives and maintain the proper domain distribution

For example: "Please create 65 multiple-choice questions based on these exam objectives, maintaining the specified domain weightings"

### Format the Questions

Ask the AI to format the questions in ExamOMatic's JSON format

Use our sample questions as a template to ensure proper formatting

The JSON structure should follow this format:

```json
{
  "exam_name": "Your Exam Name",
  "exam_code": "EXAM-001",
  "questions": [
    {
      "question": "Question text here?",
      "question_images": [],
      "options": [
        {"text": "First option", "is_correct": true},
        {"text": "Second option", "is_correct": false},
        {"text": "Third option", "is_correct": false},
        {"text": "Fourth option", "is_correct": false}
      ],
      "explanation": "Explanation of the correct answer",
      "explanation_images": []
    }
  ]
}
```

### Review and Import

Review the generated questions for accuracy and quality

Save the JSON content to a file

Import the file using ExamOMatic's import feature


This process helps create comprehensive practice exams that accurately reflect the real exam's content distribution and objectives.


