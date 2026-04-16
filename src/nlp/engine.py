"""
Engine wrapper around uralicNLP for generating inflections.
"""
from functools import lru_cache
from uralicNLP import uralicApi
from src.nlp.tags import get_noun_tag, get_verb_tag, get_participle_tag

def ensure_model_downloaded(lang="fin"):
    """Downloads the uralicNLP language model if it is not already present."""
    if not uralicApi.is_language_installed(lang):
        print(f"Downloading {lang} model for uralicNLP. This may take a few minutes...")
        uralicApi.download(lang)

@lru_cache(maxsize=4096)
def _cached_generate(query: str, lang: str) -> tuple[str, ...]:
    """Cached transducer lookup. Returns a tuple for hashability."""
    try:
        results = uralicApi.generate(query, lang)
        return tuple(res[0].split('@')[0] for res in results)
    except Exception as e:
        print(f"Error generating inflection for {query}: {e}")
        return ()

def generate_inflection(base_word: str, full_tag: str, lang: str = "fin") -> list[str]:
    """
    Generates the possible inflected forms for a base word and tag.
    Returns a list of possible string results.
    """
    return list(_cached_generate(f"{base_word}{full_tag}", lang))

def inflect_noun(base_word: str, case: str, number: str, pos: str = "N") -> list[str]:
    """Generates inflections for a noun/adjective given its case and number."""
    tag = get_noun_tag(case, number, pos)
    return generate_inflection(base_word, tag)

def inflect_verb(base_word: str, tense_mood: str, person: str) -> list[str]:
    """Generates inflections for a verb given its tense/mood and person."""
    tag = get_verb_tag(tense_mood, person)
    return generate_inflection(base_word, tag)

def inflect_participle(base_word: str, participle: str, case: str, number: str) -> list[str]:
    """Generates inflections for a verb participle declined in a given case and number."""
    tag = get_participle_tag(participle, case, number)
    return generate_inflection(base_word, tag)
