import csv
import json
import sys
from pathlib import Path
from uralicNLP import uralicApi
from platformdirs import user_data_dir

# For packaged data access
if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

APP_NAME = "finnish-inflection-cli"

_vocab_cache: dict | None = None

def classify_verb_type(lemma: str) -> int:
    """Classifies a Finnish verb lemma into verb types 1-6."""
    if lemma.endswith(("eta", "etä")):
        return 6
    if lemma.endswith(("ita", "itä")):
        return 5
    if lemma.endswith(("lla", "llä", "nna", "nnä", "rra", "rrä", "sta", "stä")):
        return 3
    if lemma.endswith(("da", "dä")):
        return 2
    if (
        len(lemma) >= 3
        and lemma[-2] == "t"
        and lemma[-1] in ("a", "ä")
        and lemma[-3] in "aeiouyäö"
    ):
        return 4
    if lemma.endswith(("a", "ä")):
        return 1
    return 0

def categorize_word(word: str, english_hint: str = "") -> tuple[str, str]:
    """Uses uralicApi to categorize a word and find its lemma."""
    try:
        analyses = uralicApi.analyze(word, "fin")
        if not analyses:
            return "?", word
        
        # Determine POS and lemma
        v_lemma = None
        a_lemma = None
        n_lemma = None
        
        # Lemmatize provides the full base word
        lemmas = uralicApi.lemmatize(word, "fin")
        primary_lemma = lemmas[0] if lemmas else word
        
        for analysis_tuple in analyses:
            analysis_str = analysis_tuple[0]
            # Skip participles/negative participles when looking for a pure Verb base
            is_participle = any(tag in analysis_str for tag in ["+PrfPrc", "+PrsPrc", "+NegPrc", "+AgPrc"])
            
            if "+V" in analysis_str and not v_lemma and not is_participle: 
                v_lemma = analysis_str.split('+')[0].replace('#', '')
            if "+A" in analysis_str and not a_lemma: a_lemma = primary_lemma
            if "+N" in analysis_str and not n_lemma: n_lemma = primary_lemma

        # Use English hint to break ties
        hint = english_hint.lower()
        pos_pref = None
        if hint.startswith("to "): pos_pref = "V"
        elif any(word in hint for word in ["(v)", "verb"]): pos_pref = "V"
        elif any(word in hint for word in ["(n)", "noun"]): pos_pref = "N"
        elif any(word in hint for word in ["(adj)", "adjective"]): pos_pref = "A"

        if pos_pref == "V" and v_lemma: return "V", v_lemma
        if pos_pref == "A" and a_lemma: return "A", a_lemma
        if pos_pref == "N" and n_lemma: return "N", n_lemma

        # Default order of preference if no strong hint
        if v_lemma and (word.endswith(("a", "ä", "da", "dä", "ta", "tä")) or pos_pref == "V"):
            return "V", v_lemma
        
        if a_lemma: return "A", a_lemma
        if n_lemma: return "N", n_lemma
        if v_lemma: return "V", v_lemma
            
    except Exception as e:
        print(f"Error categorizing '{word}': {e}")
        
    return "?", word

def load_book_of_mormon_vocab(filepath: str = None):
    """
    Loads and categorizes the BOM vocabulary based on omorfi parsing.
    Caches the result on disk and in memory.
    """
    global _vocab_cache
    if _vocab_cache is not None:
        return _vocab_cache["nouns"], _vocab_cache["verbs"]

    data_dir = Path(user_data_dir(APP_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_path = data_dir / "vocab_cache.json"
    
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nouns = data.get("nouns", [])
                verbs = data.get("verbs", [])
                cache_updated = False
                for verb in verbs:
                    if "verb_type" not in verb:
                        verb["verb_type"] = classify_verb_type(verb.get("lemma", verb.get("fin", "")))
                        cache_updated = True
                if cache_updated:
                    with open(cache_path, "w", encoding="utf-8") as wf:
                        json.dump({"nouns": nouns, "verbs": verbs}, wf, ensure_ascii=False, indent=2)
                if nouns or verbs:
                    _vocab_cache = {"nouns": nouns, "verbs": verbs}
                    return nouns, verbs
        except Exception:
            pass
            
    if filepath is None:
        csv_resource = files('src').joinpath('../book_of_mormon_complete.csv')
        if not csv_resource.exists():
            csv_resource = Path("book_of_mormon_complete.csv")
            
        if not csv_resource.exists():
            print(f"Warning: book_of_mormon_complete.csv not found.")
            return [], []
        
        with csv_resource.open(mode='r', encoding='utf-8') as f:
            return _parse_csv(f, cache_path)
    else:
        with open(filepath, mode='r', encoding='utf-8') as f:
            return _parse_csv(f, cache_path)

def _parse_csv(f, cache_path):
    global _vocab_cache
    nouns = []
    verbs = []
    print("Categorizing vocabulary using uralicNLP. This might take a few moments on the first run...")
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        front = row.get("Front", "").strip()
        back = row.get("Back", "").strip()
        if not front:
            continue
        
        category, lemma = categorize_word(front, back)
        item = {"fin": front, "lemma": lemma, "eng": back, "pos": category}
        if category in ("N", "A"):
            nouns.append(item)
        elif category == "V":
            item["verb_type"] = classify_verb_type(lemma)
            verbs.append(item)
                
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"nouns": nouns, "verbs": verbs}, f, ensure_ascii=False, indent=2)

    _vocab_cache = {"nouns": nouns, "verbs": verbs}
    return nouns, verbs

def get_nouns_list():
    nouns, _ = load_book_of_mormon_vocab()
    return nouns

def get_verbs_list():
    _, verbs = load_book_of_mormon_vocab()
    return verbs

def get_verbs_by_type(verb_types: list[int]) -> list[dict]:
    """Returns only verbs matching the selected verb types."""
    _, verbs = load_book_of_mormon_vocab()
    allowed = set(verb_types)
    return [verb for verb in verbs if verb.get("verb_type") in allowed]
