# AI Quiz Generator

Generate interactive quizzes from PowerPoint presentations using AI.

---

## What This Project Does

Upload a PPT/PPTX file and automatically generate a multiple-choice quiz based on the slide content.

The application:

* Extracts slide text
* Generates MCQs using AI
* Supports difficulty levels
* Scores answers
* Provides AI-generated explanations

---

## Project Structure

ai-quiz-generator/

├─ .env

├─ .gitignore

├─ spec.md

├─ requirements.txt

├─ app.py

├─ quiz_generator.py

├─ ppt_parser.py

└─ README.md

---

## Requirements

Python 3.11+

OpenRouter API Key

---

## Setup

### 1. Create Virtual Environment

python -m venv .venv

### 2. Activate Environment

Windows

.venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Create .env

OPENROUTER_API_KEY=your_key_here

---

## Run Application

streamlit run app.py

---

## Features

### PPT Upload

Upload PPT/PPTX files.

### Content Extraction

Extract text from slides.

### Quiz Configuration

* 5–30 questions
* Simple
* Medium
* Complex

### AI Quiz Generation

* Four options per question
* One correct answer
* AI-generated distractors

### Interactive Quiz

* Navigate questions
* Track progress
* Submit answers

### Results

* Score
* Percentage
* Correct answers
* Explanations

---

## Dependencies

python-pptx

streamlit

openai

python-dotenv

---

## Future Improvements

* PDF support
* Authentication
* Quiz history
* Leaderboards
* Adaptive learning

---

## Author

Lakshmi Vyshnavi

AI Quiz Generator

Academic Year 2025–26
