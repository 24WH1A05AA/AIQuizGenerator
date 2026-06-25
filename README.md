# AI Quiz Generator

Generate interactive multiple-choice quizzes from PowerPoint presentations using AI.

---

## What It Does

Upload a `.pptx` file and instantly generate a scored, timed quiz based on the slide content.

- Extracts text from every slide
- Sends content to an LLM via [OpenRouter](https://openrouter.ai/)
- Generates MCQs at your chosen difficulty
- Runs an interactive, timed quiz
- Scores answers and shows AI explanations

---

## Features

| Feature | Details |
|---|---|
| PPT Upload | `.ppt` / `.pptx`, magic-byte validation, corruption detection |
| Content Extraction | All slides, title-first ordering, empty-slide detection |
| Quiz Configuration | 5–30 questions · Simple / Medium / Complex difficulty |
| AI Generation | GPT-4o-mini via OpenRouter · 4 choices per question · plausible distractors |
| Quiz Interface | One question at a time · 30 s per-question timer · Previous/Next navigation |
| Question Palette | Sidebar palette with answered/unanswered/current indicators |
| Jump to Question | Selectbox in sidebar for instant navigation |
| Review Panel | Mid-quiz collapsible overview of all questions with status |
| Scoring | Percentage score · correct/incorrect breakdown · score ring |
| AI Feedback | Per-question explanation of the correct answer |
| Error Handling | Typed errors for timeout, auth failure, rate limit, malformed JSON |
| Caching | `@st.cache_data` on PPT extraction and quiz generation |
| Dark / Light Mode | Toggle in sidebar |
| Logging | Rotating file log (`quiz_generator.log`) for technical details |

---

## Project Structure

```
AIQuizGenerator/
├── app.py               # Streamlit UI (all steps, CSS, session state)
├── quiz_generator.py    # OpenRouter API, prompt, parsing, scoring
├── ppt_parser.py        # python-pptx extraction, validation, caching
├── errors.py            # Centralised rotating-file logger
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml      # Theme, upload limit, security settings
└── spec.md
```

---

## Requirements

- Python 3.11+
- An [OpenRouter API key](https://openrouter.ai/keys)

---

## Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd AIQuizGenerator

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY=<your key>
```

---

## Run

```bash
streamlit run app.py
```

---

## Deployment (Streamlit Community Cloud)

1. Push the repo to GitHub (`.env` is git-ignored).
2. In Streamlit Cloud → **New app** → select the repo.
3. Add `OPENROUTER_API_KEY` under **Settings → Secrets**.
4. Deploy — `.streamlit/config.toml` is picked up automatically.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | Your OpenRouter API key |

---

## Dependencies

```
streamlit>=1.32.0
python-pptx>=0.6.23
openai>=1.14.0
python-dotenv>=1.0.1
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Invalid file type | User-friendly message, upload blocked |
| Corrupted / password-protected PPT | Specific error, logged to file |
| Empty presentation | Specific error, upload blocked |
| Missing API key | Clear setup instructions shown |
| API auth failure | "Invalid API key" message |
| Rate limit | "Too many requests" message with retry hint |
| Timeout | "Request timed out" message |
| Malformed AI JSON | "Unexpected AI response" message, retry suggested |

---

## Future Work (Stretch Goals)

- PDF support
- Quiz export (PDF / CSV)
- Quiz history and leaderboard
- Adaptive difficulty
- Analytics dashboard
- Multi-language support

---

## Author

Lakshmi Vyshnavi — TechVest Global · Academic Year 2025–26
