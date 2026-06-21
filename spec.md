AI Quiz Generator

## Goal

Transform a PowerPoint presentation into an AI-generated interactive quiz.

The application should extract slide content from a PPT/PPTX file, generate multiple-choice questions using an LLM, allow users to take the quiz, and provide scores with AI-generated explanations.

---

## Input

### User Inputs

* PPT/PPTX file
* Number of questions (5–30)
* Difficulty level:

  * Simple
  * Medium
  * Complex

---

## Output

### Generated Quiz

For each question:

* Question text
* Four answer choices (A–D)
* One correct answer

### Results

* Final score
* Percentage score
* Correct answers
* Incorrect answers
* AI explanation for mistakes

---

## Scope

### In Scope

* PPT/PPTX upload
* Slide text extraction
* AI MCQ generation
* Difficulty filtering
* Interactive quiz UI
* Scoring system
* AI feedback

### Out of Scope

* User authentication
* Video/audio files
* Essay questions
* Multi-language support

---

## Functional Requirements

### FR-1 PPT Upload

* Accept PPT/PPTX files
* Reject unsupported formats
* Show slide count

### FR-2 Content Extraction

* Extract text from all slides
* Generate preview of extracted content

### FR-3 Quiz Configuration

* Select question count (5–30)
* Select difficulty level
* Generate quiz button

### FR-4 AI Question Generation

* Generate relevant MCQs
* Exactly four options per question
* One correct answer
* Plausible distractors

### FR-5 Quiz Interface

* One question at a time
* Previous / Next navigation
* Progress indicator
* Timer (optional)

### FR-6 Scoring

* Calculate total score
* Display percentage
* Highlight correct answers

### FR-7 Feedback

* Explain why answers are incorrect
* Show correct answer with reasoning

---

## Tech Stack

### Frontend

* Streamlit

### Backend

* Python

### AI

* OpenRouter API

### Libraries

* python-pptx
* openai
* python-dotenv

---

## Pipeline

1. Upload PPT/PPTX file.
2. Extract slide text using python-pptx.
3. Select question count and difficulty.
4. Send extracted content to LLM.
5. Generate MCQs.
6. Display interactive quiz.
7. Collect user answers.
8. Calculate score.
9. Generate AI feedback.
10. Display results.

---

## Error Handling

### Upload Errors

* Invalid file type
* Empty presentation
* Corrupted PPT

### AI Errors

* API timeout
* Invalid response format
* Question generation failure

### Quiz Errors

* Missing answers
* Session reset

---

## Done When

* PPT file uploads successfully.
* Slide text is extracted correctly.
* AI generates requested number of questions.
* Every question has 4 options.
* User can complete the quiz.
* Score is calculated correctly.
* AI explanations are shown.
* API key is stored only in .env.
* Application runs through Streamlit.

---

## Stretch Goals

* PDF support
* Quiz export
* Quiz history
* Adaptive difficulty
* Analytics dashboard
* Multi-language support
