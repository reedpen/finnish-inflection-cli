"""User-facing vocabulary import and review pipeline."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, IO, Any

from src.data.vocab import (
    VocabularyEntry,
    VocabularyDocument,
    VocabularyError,
    classify_verb_type,
    make_vocabulary_document,
)

Analyzer = Callable[[str, str], tuple[str, str]]


@dataclass(frozen=True)
class ImportPreview:
    accepted: list[VocabularyEntry]
    corrected: list[VocabularyEntry]
    ambiguous: list[dict[str, str]]
    rejected: list[dict[str, str]]
    excluded: list[str]
    document: VocabularyDocument


def _read_rows(path: Path, handle: IO[str]) -> list[tuple[str, str]]:
    if path.suffix.casefold() == ".csv":
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None or not {"Front", "Back"}.issubset(
            reader.fieldnames
        ):
            raise VocabularyError("CSV headers must include Front and Back")
        return [
            ((row.get("Front") or "").strip(), (row.get("Back") or "").strip())
            for row in reader
        ]
    if path.suffix.casefold() == ".txt":
        rows = []
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            parts = line.rstrip("\r\n").split(",", 1)
            if len(parts) != 2:
                raise VocabularyError(
                    f"text line {line_number} must be Finnish,English"
                )
            rows.append((parts[0].strip(), parts[1].strip()))
        return rows
    raise VocabularyError("vocabulary files must use .csv or .txt")


def import_vocabulary(
    source: Path | str,
    *,
    analyzer: Analyzer,
    name: str,
    overrides: dict[str, dict[str, str] | None] | None = None,
    forms_validator: Callable[[dict[str, Any]], bool] | None = None,
) -> ImportPreview:
    """Parse, analyze, and preview a source without installing it."""
    path = Path(source)
    try:
        source_bytes = path.read_bytes()
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VocabularyError(f"{path} is not valid UTF-8") from exc
    except OSError as exc:
        raise VocabularyError(f"could not read {path}: {exc}") from exc

    from io import StringIO

    rows = _read_rows(path, StringIO(text))
    accepted: list[VocabularyEntry] = []
    corrected: list[VocabularyEntry] = []
    ambiguous: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    excluded: list[str] = []
    seen: set[tuple[str, str]] = set()
    overrides = overrides or {}

    for fin, eng in rows:
        if not fin or not eng:
            rejected.append(
                {
                    "fin": fin or "(empty)",
                    "reason": "Finnish and English values are required",
                }
            )
            continue
        if fin in overrides:
            override = overrides[fin]
            if override is None:
                excluded.append(fin)
                continue
            if not isinstance(override, dict):
                raise VocabularyError(f"override for {fin!r} must be an object or null")
            pos, lemma = override.get("pos", "?"), override.get("lemma", fin)
            if not isinstance(pos, str) or not isinstance(lemma, str):
                raise VocabularyError(
                    f"override for {fin!r} must contain text lemma and pos values"
                )
            was_corrected = True
        else:
            pos, lemma = analyzer(fin, eng)
            was_corrected = False
        if pos not in {"N", "A", "V"} or not lemma:
            problem = {
                "fin": fin,
                "reason": "unknown or ambiguous analysis; add an override or exclusion",
            }
            ambiguous.append(problem)
            continue
        item: VocabularyEntry = {
            "fin": fin,
            "lemma": lemma,
            "eng": eng,
            "pos": pos,
        }
        if pos == "V":
            item["verb_type"] = classify_verb_type(lemma)
            if item["verb_type"] not in range(1, 7):
                rejected.append(
                    {"fin": fin, "reason": "recognized verb has no valid verb type"}
                )
                continue
        key = (lemma.casefold(), pos)
        if key in seen:
            rejected.append(
                {"fin": fin, "reason": "duplicate lemma and part of speech"}
            )
            continue
        if forms_validator is not None and not forms_validator(item):
            rejected.append({"fin": fin, "reason": "no generated forms"})
            continue
        seen.add(key)
        accepted.append(item)
        if was_corrected:
            corrected.append(item)

    document = make_vocabulary_document(accepted, source_bytes=source_bytes, name=name)
    return ImportPreview(accepted, corrected, ambiguous, rejected, excluded, document)


def preview_summary(preview: ImportPreview) -> str:
    return (
        f"Accepted: {len(preview.accepted)}; corrected: {len(preview.corrected)}; "
        f"ambiguous: {len(preview.ambiguous)}; rejected: {len(preview.rejected)}; "
        f"excluded: {len(preview.excluded)}"
    )


def preview_rows(preview: ImportPreview) -> list[dict[str, str]]:
    """Return display-neutral detailed rows for CLI and interactive renderers."""
    corrected = {id(item) for item in preview.corrected}
    ambiguous = {(item["fin"], item["reason"]) for item in preview.ambiguous}
    rows = []
    for item in preview.accepted:
        status = "corrected" if id(item) in corrected else "accepted"
        rows.append(
            {
                "status": status,
                "fin": item["fin"],
                "detail": f"{item['lemma']} ({item['pos']}) — {item['eng']}",
            }
        )
    rows.extend(
        {"status": "ambiguous", "fin": item["fin"], "detail": item["reason"]}
        for item in preview.ambiguous
    )
    rows.extend(
        {"status": "rejected", "fin": item["fin"], "detail": item["reason"]}
        for item in preview.rejected
        if (item["fin"], item["reason"]) not in ambiguous
    )
    rows.extend(
        {
            "status": "excluded",
            "fin": fin,
            "detail": "explicitly excluded by review",
        }
        for fin in preview.excluded
    )
    return rows


def load_overrides(path: Path | str | None) -> dict[str, dict[str, str] | None] | None:
    if path is None or str(path).strip() == "":
        return None
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VocabularyError(f"could not read overrides: {exc}") from exc
    if not isinstance(value, dict):
        raise VocabularyError("overrides must be a JSON object")
    return value


def analyze_vocabulary_source(
    source: Path | str,
    *,
    name: str,
    overrides: dict[str, dict[str, str] | None] | None = None,
    morphology=None,
) -> ImportPreview:
    """Run model setup, analysis, and a representative generated-form check."""
    from src.data.vocab import categorize_word
    from src.nlp.engine import InflectionEngine, UralicNlpAdapter
    from src.nlp.tags import get_noun_tag, get_verb_tag

    morphology = morphology or UralicNlpAdapter()
    engine = InflectionEngine(morphology)
    engine.ensure_model_downloaded("fin")

    def has_forms(entry):
        tag = (
            get_verb_tag("Present", "1st Person Sg (I)")
            if entry["pos"] == "V"
            else get_noun_tag("Nominative (---)", "Singular", entry["pos"])
        )
        return bool(engine.generate_inflection(entry["lemma"], tag))

    return import_vocabulary(
        source,
        analyzer=lambda fin, eng: categorize_word(fin, eng, morphology),
        name=name,
        overrides=overrides,
        forms_validator=has_forms,
    )
