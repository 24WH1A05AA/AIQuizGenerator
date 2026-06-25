"""AI quiz generation via OpenRouter chat completions."""

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Literal

import openai
import streamlit as st
from openai import OpenAI

from errors import log

DifficultyLevel = Literal["Simple", "Medium", "Complex"]

# ── Custom exceptions ───────────────────────────────────────────────────────
# Defined first so they can be raised anywhere in this module.


class QuizGenerationError(Exception):
    """Base class for quiz generation failures."""


class MissingAPIKeyError(QuizGenerationError):
    """OPENROUTER_API_KEY is absent from the environment."""


class APIAuthError(QuizGenerationError):
    """API key was rejected (HTTP 401/403)."""


class APIRateLimitError(QuizGenerationError):
    """Rate-limit or quota exceeded (HTTP 429)."""


class APITimeoutError(QuizGenerationError):
    """Request timed out after all retries."""


class APIConnectionError(QuizGenerationError):
    """Network-level connection failure."""


class MalformedResponseError(QuizGenerationError):
    """The AI response could not be parsed as valid quiz JSON."""


# ── Configuration ───────────────────────────────────────────────────────────
# Change OPENROUTER_MODEL to switch the underlying LLM.

OPENROUTER_MODEL = "openai/gpt-4o-mini"

_MAX_RETRIES = 3
_BASE_DELAY_S = 2.0
_TIMEOUT_S = 60.0

# ── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class Choice:
    label: str   # "A", "B", "C", or "D"
    text: str


@dataclass
class Question:
    number: int
    text: str
    choices: list[Choice]
    correct_label: str
    explanation: str = ""


@dataclass
class Quiz:
    questions: list[Question] = field(default_factory=list)
    difficulty: DifficultyLevel = "Medium"
    source_slide_count: int = 0

    @property
    def total_questions(self) -> int:
        return len(self.questions)


@dataclass
class QuestionResult:
    number: int
    question: str
    user_answer: str | None
    user_answer_text: str
    correct_answer: str
    correct_answer_text: str
    is_correct: bool
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "question": self.question,
            "selected_label": self.user_answer,
            "selected_text": self.user_answer_text,
            "correct_label": self.correct_answer,
            "correct_text": self.correct_answer_text,
            "is_correct": self.is_correct,
            "explanation": self.explanation,
        }


@dataclass
class QuizResult:
    score: int
    percentage: float
    correct_count: int
    incorrect_count: int
    total: int
    details: list[QuestionResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "percentage": self.percentage,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "total": self.total,
            "details": [d.to_dict() for d in self.details],
            "score_pct": self.percentage,  # keep app contract stable
        }


# ── Prompt template ─────────────────────────────────────────────────────────
# IMPORTANT: the JSON keys in this prompt ("choices", "correct_label") must
# match exactly what _validate_question() checks for.

_SYSTEM_PROMPT = """You are a quiz-generation assistant. Generate multiple-choice questions from the provided slide content.

## Rules
1. Generate exactly {num_questions} questions.
2. Each question must have exactly 4 choices (A, B, C, D).
3. Exactly one choice must be the correct answer.
4. Distractors must be plausible but clearly wrong.
5. Cover all major topics from the slide content — do not focus on just one section.
6. Return ONLY valid JSON — no markdown fences, no code blocks, no extra text.

## Difficulty: {difficulty}
- **Simple** — factual recall: definitions, dates, names, lists, key facts directly stated in the slides.
- **Medium** — application and understanding: why something works, how concepts relate, applying an idea to a new example.
- **Complex** — scenario-based reasoning: analyse, evaluate, or synthesise information from the slides.

## Output format (strict JSON array — no markdown, no extra keys)
[
  {{
    "question": "What is ...?",
    "choices": [
      {{"label": "A", "text": "..."}},
      {{"label": "B", "text": "..."}},
      {{"label": "C", "text": "..."}},
      {{"label": "D", "text": "..."}}
    ],
    "correct_label": "A",
    "explanation": "Because ..."
  }}
]"""


# ── Public API ──────────────────────────────────────────────────────────────


def generate_quiz(
    full_text: str,
    num_questions: int,
    difficulty: DifficultyLevel,
) -> Quiz:
    """
    Generate a multiple-choice quiz from slide text using OpenRouter.

    Parameters
    ----------
    full_text : str
        All slide text joined together.
    num_questions : int
        Number of questions to generate (5–30).
    difficulty : DifficultyLevel
        "Simple", "Medium", or "Complex".

    Returns
    -------
    Quiz

    Raises
    ------
    MissingAPIKeyError   – OPENROUTER_API_KEY not set
    APIAuthError         – key rejected by OpenRouter
    APIRateLimitError    – rate limit hit after retries
    APITimeoutError      – request timed out after retries
    APIConnectionError   – network failure after retries
    MalformedResponseError – AI response could not be parsed
    QuizGenerationError  – any other generation failure
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "OPENROUTER_API_KEY is not set. "
            "Create a .env file with OPENROUTER_API_KEY=your_key or set the environment variable."
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=_TIMEOUT_S,
    )

    system_prompt = _SYSTEM_PROMPT.format(
        num_questions=num_questions,
        difficulty=difficulty,
    )
    user_prompt = (
        f"Generate {num_questions} {difficulty} multiple-choice questions "
        f"based on the following slide content.\n\n---\n{full_text}\n---"
    )

    raw_json = _call_with_retries(client, system_prompt, user_prompt)
    questions_data = _parse_response(raw_json, num_questions)

    questions = [
        Question(
            number=i,
            text=qd["question"],
            choices=[Choice(label=c["label"], text=c["text"]) for c in qd["choices"]],
            correct_label=qd["correct_label"],
            explanation=qd.get("explanation", ""),
        )
        for i, qd in enumerate(questions_data, start=1)
    ]
    return Quiz(questions=questions, difficulty=difficulty)


@st.cache_data(show_spinner=False)
def generate_quiz_cached(
    full_text: str,
    num_questions: int,
    difficulty: DifficultyLevel,
) -> Quiz:
    """
    Cached wrapper around generate_quiz.

    Streamlit hashes (full_text, num_questions, difficulty) as the cache key.
    Identical inputs return the cached Quiz with zero API calls.
    Exceptions propagate to the caller unchanged.
    """
    return generate_quiz(full_text, num_questions, difficulty)


# ── Retry logic ─────────────────────────────────────────────────────────────


def _call_with_retries(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    """
    Call the OpenRouter API with exponential-backoff retries.

    Raises specific QuizGenerationError subclasses so callers can show
    targeted user-friendly messages.
    """
    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
                extra_headers={
                    "HTTP-Referer": "https://github.com/24WH1A05AA/AIQuizGenerator",
                    "X-Title": "AI Quiz Generator",
                },
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                log.warning("Attempt %d/%d: API returned empty response", attempt, _MAX_RETRIES)
                last_exc = QuizGenerationError("API returned empty response")
                _maybe_sleep(attempt)
                continue
            return content.strip()

        except openai.AuthenticationError as exc:
            log.error("API authentication error: %s", exc)
            raise APIAuthError("API key was rejected by OpenRouter.") from exc

        except openai.RateLimitError as exc:
            log.warning("Attempt %d/%d: Rate-limit hit: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
            _maybe_sleep(attempt)

        except openai.APITimeoutError as exc:
            log.warning("Attempt %d/%d: Request timed out: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
            _maybe_sleep(attempt)

        except openai.APIConnectionError as exc:
            log.warning("Attempt %d/%d: Connection error: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
            _maybe_sleep(attempt)

        except openai.APIStatusError as exc:
            log.error("Attempt %d/%d: API status %s: %s", attempt, _MAX_RETRIES, exc.status_code, exc)
            last_exc = exc
            _maybe_sleep(attempt)

        except Exception as exc:
            log.error("Attempt %d/%d: Unexpected: %s", attempt, _MAX_RETRIES, exc, exc_info=True)
            last_exc = exc
            _maybe_sleep(attempt)

    # Classify the final error into a specific exception type
    if isinstance(last_exc, openai.RateLimitError):
        raise APIRateLimitError(
            f"OpenRouter rate limit reached after {_MAX_RETRIES} attempts."
        ) from last_exc
    if isinstance(last_exc, openai.APITimeoutError):
        raise APITimeoutError(
            f"Request timed out after {_MAX_RETRIES} attempts ({_TIMEOUT_S}s each)."
        ) from last_exc
    if isinstance(last_exc, openai.APIConnectionError):
        raise APIConnectionError(
            f"Could not reach OpenRouter after {_MAX_RETRIES} attempts."
        ) from last_exc
    raise QuizGenerationError(
        f"OpenRouter API call failed after {_MAX_RETRIES} retries. Last error: {last_exc}"
    ) from last_exc


def _maybe_sleep(attempt: int) -> None:
    """Exponential backoff between retries. No-op on the last attempt."""
    if attempt < _MAX_RETRIES:
        time.sleep(_BASE_DELAY_S * (2 ** (attempt - 1)))


# ── Response parsing ────────────────────────────────────────────────────────


def _parse_response(raw: str, expected_count: int) -> list[dict]:
    """
    Parse the raw LLM string into a validated list of question dicts.

    Handles markdown fences, extra whitespace, wrong question counts, and
    malformed JSON. Raises MalformedResponseError on any failure.
    """
    data = _extract_json_array(_strip_fences(raw).strip())

    if data is None or not isinstance(data, list):
        log.error("Could not extract JSON array. Raw: %s", raw[:500])
        raise MalformedResponseError(
            "The AI returned a response that could not be parsed as quiz questions."
        )

    if len(data) != expected_count:
        log.warning("Expected %d questions, got %d. Raw: %s", expected_count, len(data), raw[:300])
        raise MalformedResponseError(
            f"The AI generated {len(data)} question(s) instead of the requested {expected_count}."
        )

    return [_validate_question(item, idx) for idx, item in enumerate(data)]


def _strip_fences(text: str) -> str:
    """Remove opening and closing markdown code fences."""
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$",        "", text, flags=re.IGNORECASE)
    return text


def _extract_json_array(text: str) -> list | None:
    """Try direct JSON parse, then fall back to extracting the first [...] block."""
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _validate_question(item: dict, idx: int) -> dict:
    """Validate and normalise one question dict from the AI response."""
    # Required top-level keys — must match the prompt's JSON schema
    for key in ("question", "choices", "correct_label"):
        if key not in item:
            raise MalformedResponseError(
                f"Question {idx + 1} is missing required field '{key}'."
            )

    question_text = item["question"]
    if not isinstance(question_text, str) or not question_text.strip():
        raise MalformedResponseError(f"Question {idx + 1} has an empty 'question' field.")

    choices = item["choices"]
    if not isinstance(choices, list) or len(choices) != 4:
        raise MalformedResponseError(
            f"Question {idx + 1} must have exactly 4 choices, "
            f"got {len(choices) if isinstance(choices, list) else type(choices).__name__}."
        )

    valid_labels = {"A", "B", "C", "D"}
    seen: set[str] = set()
    for ci, choice in enumerate(choices):
        if not isinstance(choice, dict):
            raise MalformedResponseError(f"Question {idx + 1}, choice {ci + 1} is not a dict.")
        label = choice.get("label", "")
        text  = choice.get("text", "")
        if label not in valid_labels:
            raise MalformedResponseError(f"Question {idx + 1}, choice {ci + 1} has invalid label '{label}'.")
        if label in seen:
            raise MalformedResponseError(f"Question {idx + 1} has duplicate label '{label}'.")
        seen.add(label)
        if not isinstance(text, str) or not text.strip():
            raise MalformedResponseError(f"Question {idx + 1}, choice {label} has empty 'text'.")

    correct = item["correct_label"]
    if correct not in valid_labels:
        raise MalformedResponseError(f"Question {idx + 1} has invalid correct_label '{correct}'.")

    return {
        "question":      question_text.strip(),
        "choices":       choices,
        "correct_label": correct,
        "explanation":   item.get("explanation", ""),
    }


# ── Scoring ─────────────────────────────────────────────────────────────────


def get_choice_text(question: Question, label: str | None) -> str:
    """Return the text for a choice label, or '' if not found."""
    if label is None:
        return ""
    return next((c.text for c in question.choices if c.label == label), "")


def score_question(question: Question, user_answer: str | None) -> QuestionResult:
    """Score a single question against the user's answer."""
    return QuestionResult(
        number=question.number,
        question=question.text,
        user_answer=user_answer,
        user_answer_text=get_choice_text(question, user_answer),
        correct_answer=question.correct_label,
        correct_answer_text=get_choice_text(question, question.correct_label),
        is_correct=user_answer == question.correct_label,
        explanation=question.explanation,
    )


def calculate_percentage(score: int, total: int) -> float:
    """Return percentage rounded to one decimal place."""
    return round((score / total) * 100, 1) if total > 0 else 0.0


def build_quiz_result(question_results: list[QuestionResult]) -> QuizResult:
    """Aggregate per-question results into a QuizResult."""
    total         = len(question_results)
    correct_count = sum(1 for r in question_results if r.is_correct)
    return QuizResult(
        score=correct_count,
        percentage=calculate_percentage(correct_count, total),
        correct_count=correct_count,
        incorrect_count=total - correct_count,
        total=total,
        details=question_results,
    )


def score_quiz(quiz: Quiz, user_answers: dict[int, str]) -> dict:
    """
    Score all quiz answers and return a serialisable result dict.

    Parameters
    ----------
    quiz : Quiz
    user_answers : {question_number: selected_label}

    Returns
    -------
    dict with keys: score, percentage, correct_count, incorrect_count,
                    total, details (list of per-question dicts), score_pct
    """
    results = [score_question(q, user_answers.get(q.number)) for q in quiz.questions]
    return build_quiz_result(results).to_dict()
