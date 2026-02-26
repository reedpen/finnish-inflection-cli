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

def categorize_word(word: str, english_hint: str = "") -> tuple[str, str]:
    """Uses uralicApi to categorize a word and find its lemma."""
    try:
        if not uralicApi.is_language_installed("fin"):
            if word.endswith(("a", "ä", "da", "dä", "ta", "tä")):
                return "V", word
            return "N", word

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
    Caches the result in the user's data directory.
    """
    data_dir = Path(user_data_dir(APP_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_path = data_dir / "vocab_cache.json"
    
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nouns = data.get("nouns", [])
                verbs = data.get("verbs", [])
                if len(nouns) > 0 or len(verbs) > 0:
                    return nouns, verbs
        except Exception:
            pass
            
    # If no cache or cache failed, load from CSV
    if filepath is None:
        # Look for the file in the project root (dev) or packaged location
        # When installed as a package, it should be in the root of the install
        # Hatch sdist/wheel config puts it in the root.
        # importlib.resources.files('src') refers to the src/ directory.
        # But our CSV is in the root. We can use a trick to find it relative to 'src'.
        csv_resource = files('src').joinpath('../book_of_mormon_complete.csv')
        if not csv_resource.exists():
            # Fallback for development if run from root
            csv_resource = Path("book_of_mormon_complete.csv")
            
        if not csv_resource.exists():
            print(f"Warning: book_of_mormon_complete.csv not found.")
            return [], []
        
        # Open the resource context
        with csv_resource.open(mode='r', encoding='utf-8') as f:
            return _parse_csv(f, cache_path)
    else:
        with open(filepath, mode='r', encoding='utf-8') as f:
            return _parse_csv(f, cache_path)

def _parse_csv(f, cache_path):
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
        if category == "N" or category == "A":
            nouns.append(item)
        elif category == "V":
            verbs.append(item)
                
    # Cache the result
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"nouns": nouns, "verbs": verbs}, f, ensure_ascii=False, indent=2)
        
    return nouns, verbs

def get_nouns_list():
    nouns, _ = load_book_of_mormon_vocab()
    return nouns

def get_verbs_list():
    _, verbs = load_book_of_mormon_vocab()
    return verbs
