"""Build finite pools of questions that the inflection engine can answer."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import random

from src.data.vocab import VocabularyEntry


Inflector = Callable[..., list[str]]


@dataclass(frozen=True)
class Question:
    """A playable prompt and its accepted answers."""

    id: str
    kind: str
    word: str
    translation: str
    target: str
    answers: tuple[str, ...]


def _answers(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _noun_combinations(cases: Iterable[str], numbers: Iterable[str]):
    """Yield each meaningful case/number combination once."""
    seen = set()
    numbers = tuple(numbers)
    for case in cases:
        if case.startswith("Instructive"):
            allowed_numbers = ("Plural",) if "Plural" in numbers else ()
        elif case.startswith("Comitative"):
            # Omorfi requires a number internally, although Finnish comitative
            # has no singular/plural contrast.
            allowed_numbers = ("Plural",)
        else:
            allowed_numbers = numbers
        for number in allowed_numbers:
            combination = (case, number)
            if combination not in seen:
                seen.add(combination)
                yield combination


def _candidate_indices(total: int, maximum: int, rng) -> Iterable[int]:
    if total <= maximum:
        return range(total)
    return (rng or random.Random()).sample(range(total), maximum)


def _build_from_candidates(
    total: int,
    scan_limit: int,
    max_questions: int,
    rng,
    make_question: Callable[[int], Question | None],
) -> list[Question]:
    """Scan a bounded sample, falling back only to avoid a false empty pool."""
    primary = tuple(_candidate_indices(total, scan_limit, rng))
    pool = []
    seen_ids = set()

    def scan(indices, *, stop_after_first: bool = False) -> bool:
        for index in indices:
            question = make_question(index)
            if question is None or question.id in seen_ids:
                continue
            seen_ids.add(question.id)
            pool.append(question)
            if len(pool) >= max_questions or stop_after_first:
                return True
        return False

    if scan(primary):
        return pool
    if not pool and len(primary) < total:
        sampled = set(primary)
        scan(
            (index for index in range(total) if index not in sampled),
            stop_after_first=True,
        )
    return pool


def build_noun_pool(
    vocabulary: Iterable[VocabularyEntry],
    cases: Iterable[str],
    numbers: Iterable[str],
    inflect: Inflector,
    *,
    max_questions: int = 100,
    max_candidates: int | None = None,
    rng=None,
) -> list[Question]:
    combinations = list(_noun_combinations(cases, numbers))
    words = list(vocabulary)
    total = len(words) * len(combinations)
    scan_limit = max_candidates or max(100, max_questions * 10)

    def make_question(index):
        word = words[index // len(combinations)]
        case, number = combinations[index % len(combinations)]
        lemma = word.get("lemma", word["fin"])
        pos = word.get("pos", "N")
        answers = _answers(inflect(lemma, case, number, pos))
        if not answers:
            return None
        question_id = f"noun:{lemma}:{pos}:{case}:{number}"
        display_number = "" if case.startswith("Comitative") else f" {number}"
        return Question(
            id=question_id,
            kind="Word",
            word=word["fin"],
            translation=word.get("eng", ""),
            target=f"{case}{display_number}",
            answers=answers,
        )

    return _build_from_candidates(total, scan_limit, max_questions, rng, make_question)


def build_verb_pool(
    vocabulary: Iterable[VocabularyEntry],
    tenses: Iterable[str],
    persons: Iterable[str],
    inflect: Inflector,
    *,
    max_questions: int = 100,
    max_candidates: int | None = None,
    rng=None,
) -> list[Question]:
    words = list(vocabulary)
    combinations = [(tense, person) for tense in tenses for person in persons]
    total = len(words) * len(combinations)
    scan_limit = max_candidates or max(100, max_questions * 10)

    def make_question(index):
        word = words[index // len(combinations)]
        tense, person = combinations[index % len(combinations)]
        lemma = word.get("lemma", word["fin"])
        answers = _answers(inflect(lemma, tense, person))
        if not answers:
            return None
        return Question(
            id=f"verb:{lemma}:{tense}:{person}",
            kind="Verb",
            word=word["fin"],
            translation=word.get("eng", ""),
            target=f"{tense}, {person}",
            answers=answers,
        )

    return _build_from_candidates(total, scan_limit, max_questions, rng, make_question)


def build_participle_pool(
    vocabulary: Iterable[VocabularyEntry],
    participles: Iterable[str],
    cases: Iterable[str],
    numbers: Iterable[str],
    inflect: Inflector,
    *,
    max_questions: int = 100,
    max_candidates: int | None = None,
    rng=None,
) -> list[Question]:
    declensions = list(_noun_combinations(cases, numbers))
    combinations = [
        (participle, case, number)
        for participle in participles
        for case, number in declensions
    ]
    words = list(vocabulary)
    total = len(words) * len(combinations)
    scan_limit = max_candidates or max(100, max_questions * 10)

    def make_question(index):
        word = words[index // len(combinations)]
        participle, case, number = combinations[index % len(combinations)]
        lemma = word.get("lemma", word["fin"])
        answers = _answers(inflect(lemma, participle, case, number))
        if not answers:
            return None
        question_id = f"participle:{lemma}:{participle}:{case}:{number}"
        display_number = "" if case.startswith("Comitative") else f" {number}"
        return Question(
            id=question_id,
            kind="Verb",
            word=word["fin"],
            translation=word.get("eng", ""),
            target=f"{participle}, {case}{display_number}",
            answers=answers,
        )

    return _build_from_candidates(total, scan_limit, max_questions, rng, make_question)
