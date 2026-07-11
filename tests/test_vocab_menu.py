from src.data.importer import ImportPreview
from src.data.vocab import VocabularyStore, make_vocabulary_document
from src.ui import vocabulary as menu


def document(fin="koira"):
    return make_vocabulary_document(
        [{"fin": fin, "lemma": fin, "eng": "dog", "pos": "N"}],
        source_bytes=fin.encode(),
        name="lesson",
    )


class Answer:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


def test_listing_marks_default_or_selected_custom_set(tmp_path):
    store = VocabularyStore(tmp_path)
    store.install("lesson", document())

    assert menu.vocabulary_listing(store) == [
        {"name": "default", "selected": True, "entries": "built-in"},
        {"name": "lesson", "selected": False, "entries": 1},
    ]

    store.select("lesson")
    assert [
        row["name"] for row in menu.vocabulary_listing(store) if row["selected"]
    ] == ["lesson"]


def test_interactive_manager_selects_a_custom_set(monkeypatch, tmp_path):
    store = VocabularyStore(tmp_path)
    store.install("lesson", document())
    replies = iter(["select", "lesson", "back"])
    monkeypatch.setattr(menu.inquirer, "select", lambda **_: Answer(next(replies)))

    assert menu.manage_vocabulary(store) is False
    assert store.selected_name() == "lesson"


def test_interactive_import_previews_confirms_and_installs(monkeypatch, tmp_path):
    store = VocabularyStore(tmp_path)
    imported = document("kissa")
    preview = ImportPreview(imported["entries"], [], [], [], [], imported)
    text_replies = iter(["lesson", "words.csv", ""])
    monkeypatch.setattr(menu.inquirer, "text", lambda **_: Answer(next(text_replies)))
    monkeypatch.setattr(menu.inquirer, "confirm", lambda **_: Answer(True))
    monkeypatch.setattr(menu, "analyze_vocabulary_source", lambda *_, **__: preview)

    menu._import_vocabulary_interactively(store)

    assert store.load("lesson")["entries"][0]["fin"] == "kissa"
