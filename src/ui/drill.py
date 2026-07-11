"""Shared terminal interaction for all practice drills."""

from dataclasses import dataclass

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console

from src.domain.interaction import InputAction, parse_input
from src.domain.questions import Question
from src.domain.session import (
    AnswerOutcome,
    OutcomeAction,
    PracticeSession,
    SessionAction,
)


console = Console()
session = PromptSession(history=InMemoryHistory())
COMMAND_HELP = "h/hint · s/skip or Enter · b/back · q/quit · Ctrl+C back · Ctrl+D quit"


@dataclass(frozen=True)
class SessionResult:
    action: SessionAction
    summary: str


def clear_terminal(output: Console | None = None) -> None:
    """Clear terminals without writing control codes to redirected output."""
    output = output or console
    if output.is_terminal:
        output.clear()


def get_hint(
    hint_level: int, last_attempt: str, answers: list[str] | tuple[str, ...]
) -> str:
    """Return a progressive hint, using the answer closest to the last attempt."""
    answer = answers[0]
    if last_attempt:
        best_answer = answers[0]
        best_prefix_len = 0
        for candidate in answers:
            prefix_len = 0
            for actual, expected in zip(last_attempt.casefold(), candidate.casefold()):
                if actual != expected:
                    break
                prefix_len += 1
            if prefix_len > best_prefix_len:
                best_prefix_len = prefix_len
                best_answer = candidate
        if len(last_attempt) > best_prefix_len:
            return f"'{last_attempt[best_prefix_len]}' at position {best_prefix_len + 1} is wrong"
        answer = best_answer
    reveal_count = min(hint_level, len(answer))
    return f"{answer[:reveal_count]}{'_' * (len(answer) - reveal_count)}  ({len(answer)} letters)"


def ask_question(
    question: Question,
    *,
    prompt_session: PromptSession | None = None,
    output: Console | None = None,
) -> tuple[AnswerOutcome, str]:
    """Ask one question using the command vocabulary shared by every drill."""
    prompt_session = prompt_session or session
    output = output or console
    output.print(
        f"\n[bold blue]{question.kind}:[/bold blue] {question.word} ({question.translation})"
    )
    output.print(f"[bold blue]Target:[/bold blue] {question.target}")
    output.print(f"[dim]{COMMAND_HELP}[/dim]")

    accepted = {answer.casefold() for answer in question.answers}
    hints = 0
    attempts = 0
    last_attempt = ""
    while True:
        try:
            raw = prompt_session.prompt("Answer: ")
        except KeyboardInterrupt:
            return AnswerOutcome.back(attempts, hints), "Returning to the drill menu."
        except EOFError:
            return AnswerOutcome.quit(attempts, hints), "Goodbye."

        value = "" if raw is None else raw.strip()
        action = parse_input(value)
        if action == InputAction.HINT:
            hints += 1
            output.print(
                f"[yellow]Hint: {get_hint(hints, last_attempt, question.answers)}[/yellow]"
            )
        elif action == InputAction.SKIP:
            return AnswerOutcome.skipped(attempts, hints), _answer_message(question)
        elif action == InputAction.BACK:
            return AnswerOutcome.back(attempts, hints), "Returning to the drill menu."
        elif action == InputAction.QUIT:
            return AnswerOutcome.quit(attempts, hints), "Goodbye."
        elif value.casefold() in accepted:
            return AnswerOutcome.correct(
                attempts + 1, hints
            ), "[bold green]Correct![/bold green] 🎉"
        else:
            attempts += 1
            last_attempt = value
            output.print("[red]Incorrect, try again.[/red]")


def _answer_message(question: Question) -> str:
    return (
        f"The correct form(s): [bold green]{', '.join(question.answers)}[/bold green]"
    )


def run_practice_session(
    questions: list[Question],
    length: int | None,
    title: str,
) -> SessionResult:
    """Run a bounded or endless practice session and display its outcome."""
    practice = PracticeSession(questions, length)
    feedback = ""
    exit_action = SessionAction.COMPLETE
    while question := practice.next_question():
        clear_terminal()
        console.print(f"[bold magenta]--- {title} ---[/bold magenta]")
        console.print(f"[dim]Progress: {practice.progress}[/dim]")
        if feedback:
            console.print(feedback)
        outcome, feedback = ask_question(question)
        practice.record(outcome)
        if outcome.action in {OutcomeAction.BACK, OutcomeAction.QUIT}:
            exit_action = SessionAction(outcome.action.value)
            break

    summary = practice.summary(exit_action)
    console.print(f"\n[bold cyan]{summary}[/bold cyan]")
    return SessionResult(exit_action, summary)
