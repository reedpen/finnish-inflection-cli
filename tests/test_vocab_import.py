import pytest

from src.data.importer import ImportPreview, import_vocabulary, preview_rows
from src.data.vocab import VocabularyError


def test_csv_import_previews_accepted_duplicates_and_unknown_words(tmp_path):
    source = tmp_path / "words.csv"
    source.write_text(
        "Front;Back\nkoira;dog\nkoira;hound\nxyz;unknown\n", encoding="utf-8"
    )

    preview = import_vocabulary(
        source,
        analyzer=lambda fin, eng: ("N", "koira") if fin == "koira" else ("?", fin),
        name="lesson",
    )

    assert [item["fin"] for item in preview.accepted] == ["koira"]
    assert preview.rejected == [
        {"fin": "koira", "reason": "duplicate lemma and part of speech"},
    ]
    assert preview.ambiguous == [
        {
            "fin": "xyz",
            "reason": "unknown or ambiguous analysis; add an override or exclusion",
        },
    ]
    assert preview.document["metadata"]["name"] == "lesson"


def test_ambiguous_word_requires_checked_override_or_exclusion(tmp_path):
    source = tmp_path / "words.txt"
    source.write_text("kuusi,six or spruce\npois,away\n", encoding="utf-8")

    preview = import_vocabulary(
        source,
        analyzer=lambda *_: ("?", ""),
        overrides={"kuusi": {"pos": "N", "lemma": "kuusi"}, "pois": None},
        name="reviewed",
    )

    assert preview.corrected == [
        {"fin": "kuusi", "lemma": "kuusi", "eng": "six or spruce", "pos": "N"}
    ]
    assert preview.excluded == ["pois"]
    assert preview.rejected == []


def test_import_rejects_wrong_csv_headers_and_invalid_utf8(tmp_path):
    wrong = tmp_path / "wrong.csv"
    wrong.write_text("Finnish;English\nkoira;dog\n", encoding="utf-8")
    with pytest.raises(VocabularyError, match="Front.*Back"):
        import_vocabulary(wrong, analyzer=lambda *_: ("N", "koira"), name="x")

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"koira,\xff")
    with pytest.raises(VocabularyError, match="UTF-8"):
        import_vocabulary(invalid, analyzer=lambda *_: ("N", "koira"), name="x")


def test_unproducible_forms_are_reported(tmp_path):
    source = tmp_path / "words.txt"
    source.write_text("koira,dog\n", encoding="utf-8")

    preview = import_vocabulary(
        source,
        analyzer=lambda *_: ("N", "koira"),
        forms_validator=lambda entry: False,
        name="x",
    )

    assert preview.accepted == []
    assert preview.rejected == [{"fin": "koira", "reason": "no generated forms"}]


@pytest.mark.parametrize("override", ["noun", {"lemma": 42, "pos": "N"}])
def test_malformed_overrides_are_actionable(tmp_path, override):
    source = tmp_path / "words.txt"
    source.write_text("koira,dog\n", encoding="utf-8")

    with pytest.raises(VocabularyError, match="override.*koira"):
        import_vocabulary(
            source,
            analyzer=lambda *_: ("N", "koira"),
            overrides={"koira": override},
            name="x",
        )


def test_preview_rows_detail_each_review_category():
    accepted = {"fin": "koira", "lemma": "koira", "eng": "dog", "pos": "N"}
    corrected = {
        "fin": "puhun",
        "lemma": "puhua",
        "eng": "speak",
        "pos": "V",
        "verb_type": 1,
    }
    preview = ImportPreview(
        accepted=[accepted, corrected],
        corrected=[corrected],
        ambiguous=[{"fin": "kuusi", "reason": "multiple analyses"}],
        rejected=[{"fin": "(empty)", "reason": "required"}],
        excluded=["pois"],
        document={},
    )

    assert preview_rows(preview) == [
        {"status": "accepted", "fin": "koira", "detail": "koira (N) — dog"},
        {
            "status": "corrected",
            "fin": "puhun",
            "detail": "puhua (V) — speak",
        },
        {"status": "ambiguous", "fin": "kuusi", "detail": "multiple analyses"},
        {"status": "rejected", "fin": "(empty)", "detail": "required"},
        {
            "status": "excluded",
            "fin": "pois",
            "detail": "explicitly excluded by review",
        },
    ]


def test_preview_rows_does_not_repeat_an_ambiguous_rejection():
    problem = {"fin": "kuusi", "reason": "multiple analyses"}
    preview = ImportPreview(
        accepted=[],
        corrected=[],
        ambiguous=[problem],
        rejected=[problem],
        excluded=[],
        document={},
    )

    assert preview_rows(preview) == [
        {"status": "ambiguous", "fin": "kuusi", "detail": "multiple analyses"}
    ]
