import csv
import os
import json
from pathlib import Path
from uralicNLP import uralicApi

CACHE_FILE = Path("data/vocab_cache.json")

def categorize_word(word: str) -> tuple[str, str]:
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
        
        # Lemmatize provides the full base word (e.g. 'hallituskausi' instead of 'hallitus')
        lemmas = uralicApi.lemmatize(word, "fin")
        primary_lemma = lemmas[0] if lemmas else word
        
        for analysis_tuple in analyses:
            analysis_str = analysis_tuple[0]
            # If we find a specific POS, we try to use the lemmatize result
            if "+V" in analysis_str and not v_lemma: v_lemma = primary_lemma
            if "+A" in analysis_str and not a_lemma: a_lemma = primary_lemma
            if "+N" in analysis_str and not n_lemma: n_lemma = primary_lemma
        
        # Order of preference for drills
        if v_lemma: return "V", v_lemma
        if a_lemma: return "A", a_lemma
        if n_lemma: return "N", n_lemma
            
    except Exception as e:
        print(f"Error categorizing '{word}': {e}")
        
    return "?", word

def load_book_of_mormon_vocab(filepath: str = "book_of_mormon_complete.csv"):
    """
    Loads and categorizes the BOM vocabulary based on omorfi parsing.
    Caches the result to avoid parsing thousands of words every startup.
    """
    # Create data directory if it doesn't exist
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            nouns = data.get("nouns", [])
            verbs = data.get("verbs", [])
            if len(nouns) > 0 or len(verbs) > 0:
                return nouns, verbs
            else:
                print("Cache appears empty. Reparsing...")
            
    path = Path(filepath)
    if not path.exists():
        print(f"Warning: {filepath} not found.")
        return [], []
        
    nouns = []
    verbs = []
    
    print("Categorizing vocabulary using uralicNLP. This might take a few moments on the first run...")
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            front = row.get("Front", "").strip()
            back = row.get("Back", "").strip()
            if not front:
                continue
            
            category, lemma = categorize_word(front)
            # Store the lemma for inflection, but keep original 'front' for display if needed
            item = {"fin": front, "lemma": lemma, "eng": back, "pos": category}
            if category == "N" or category == "A":
                nouns.append(item)
            elif category == "V":
                verbs.append(item)
                
    # Cache the result
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"nouns": nouns, "verbs": verbs}, f, ensure_ascii=False, indent=2)
        
    return nouns, verbs

def get_nouns_list():
    nouns, _ = load_book_of_mormon_vocab()
    return nouns

def get_verbs_list():
    _, verbs = load_book_of_mormon_vocab()
    return verbs
