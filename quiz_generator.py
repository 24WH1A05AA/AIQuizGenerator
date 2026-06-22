"""AI quiz generation via OpenRouter (stub — AI not yet implemented)."""

from dataclasses import dataclass, field
from typing import Literal

DifficultyLevel = Literal["Simple", "Medium", "Complex"]


@dataclass
class Choice:
    label: str   # "A", "B", "C", "D"
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


def generate_quiz(
    full_text: str,
    num_questions: int,
    difficulty: DifficultyLevel,
) -> Quiz:
    """
    Generate a multiple-choice quiz from slide text.

    AI integration is not yet implemented — returns placeholder questions
    so the rest of the UI can be exercised end-to-end.
    """
    questions = _generate_placeholder_questions(num_questions, difficulty)
    return Quiz(questions=questions, difficulty=difficulty)


def _generate_placeholder_questions(
    num_questions: int,
    difficulty: DifficultyLevel,
) -> list[Question]:
    """Return dummy questions used until AI is wired up."""
    questions = []
    for i in range(1, num_questions + 1):
        choices = [
            Choice("A", f"Option A for question {i}"),
            Choice("B", f"Option B for question {i}"),
            Choice("C", f"Option C for question {i}"),
            Choice("D", f"Option D for question {i}"),
        ]
        questions.append(
            Question(
                number=i,
                text=f"[{difficulty}] Placeholder question {i} — AI not yet connected.",
                choices=choices,
                correct_label="A",
                explanation="This is a placeholder explanation. AI will provide real feedback.",
            )
        )
    return questions


def score_quiz(quiz: Quiz, user_answers: dict[int, str]) -> dict:
    """
    Score user answers against correct answers.

    user_answers: {question_number: selected_label}

    Returns:
        correct_count, incorrect_count, score_pct,
        details: list of per-question result dicts
    """
    details = []
    correct_count = 0

    for q in quiz.questions:
        selected = user_answers.get(q.number)
        is_correct = selected == q.correct_label

        if is_correct:
            correct_count += 1

        selected_text = ""
        correct_text = ""
        for choice in q.choices:
            if choice.label == selected:
                selected_text = choice.text
            if choice.label == q.correct_label:
                correct_text = choice.text

        details.append({
            "number": q.number,
            "question": q.text,
            "selected_label": selected,
            "selected_text": selected_text,
            "correct_label": q.correct_label,
            "correct_text": correct_text,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    total = quiz.total_questions
    incorrect_count = total - correct_count
    score_pct = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "total": total,
        "score_pct": score_pct,
        "details": details,
    }
