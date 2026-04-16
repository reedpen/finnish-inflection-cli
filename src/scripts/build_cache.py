import sys
import os
import csv
import json
from pathlib import Path
from rich.console import Console
from rich.progress import track

# Add src to pythonpath so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from uralicNLP import uralicApi
from src.nlp.tags import NOUN_CASES, NOUN_NUMBERS, VERB_TENSES_MOODS, VERB_PERSONS, VERB_PARTICIPLES, get_noun_tag, get_verb_tag, get_participle_tag
from src.data.vocab import classify_verb_type

console = Console()

def ensure_model_downloaded(lang="fin"):
    if not uralicApi.is_language_installed(lang):
        console.print(f"[bold yellow]Downloading {lang} model for uralicNLP. This may take a few minutes...[/bold yellow]")
        uralicApi.download(lang)

def categorize_word(word: str) -> str:
    """Uses uralicApi to categorize a word directly."""
    try:
        analyses = uralicApi.analyze(word, "fin")
        if not analyses:
            return "?"
        
        tags = set()
        for analysis_tuple in analyses:
            parts = analysis_tuple[0]
            for part in parts:
                if isinstance(part, str) and part.startswith('+'):
                    tags.add(part)
        
        if "+N" in tags and "+V" not in tags: return "N"
        if "+V" in tags and "+N" not in tags: return "V"
        if "+N" in tags: return "N"
        elif "+V" in tags: return "V"
    except Exception:
        pass
    return "?"

def generate_forms(base_word: str, full_tag: str, lang: str = "fin") -> list[str]:
    query = f"{base_word}{full_tag}"
    try:
        results = uralicApi.generate(query, lang)
        return list(set([res[0].split('@')[0] for res in results]))
    except Exception:
        return []

def build_cache(input_filepath: str, output_filepath: str = "data/vocab_cache.json"):
    path = Path(input_filepath)
    if not path.exists():
        console.print(f"[bold red]Error: Could not find file {input_filepath}[/bold red]")
        return False
        
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]Loading uralicNLP model (this takes ~1-2 mins to boot silently)...[/bold blue]")
    ensure_model_downloaded("fin")
    
    # Pre-ping uralicApi to force it to load into memory
    uralicApi.analyze("boot", "fin") 
    console.print(f"[bold green]uralicNLP Model Loaded![/bold green]")
    
    raw_words = []
    
    # Try parsing CSV if it's a CSV with front/back
    if path.suffix.lower() == '.csv':
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    front = row.get("Front", "").strip()
                    back = row.get("Back", "").strip()
                    if front:
                        raw_words.append({"fin": front, "eng": back})
        except Exception as e:
            console.print(f"[red]Error parsing CSV: {e}[/red]")
            return False
    # Try generic txt parser
    elif path.suffix.lower() in ['.txt']:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        raw_words.append({"fin": parts[0].strip(), "eng": parts[1].strip()})
                    elif len(parts) == 1 and parts[0].strip():
                        raw_words.append({"fin": parts[0].strip(), "eng": ""})
        except Exception as e:
            console.print(f"[red]Error parsing TXT: {e}[/red]")
            return False
            
    if not raw_words:
        console.print("[red]No words found in the provided file.[/red]")
        return False
        
    nouns = []
    verbs = []
    skipped = 0
    
    console.print(f"[cyan]Processing {len(raw_words)} words...[/cyan]")
    for item in track(raw_words, description="Compiling inflections:"):
        fin_word = item["fin"]
        cat = categorize_word(fin_word)
        
        if cat == "N":
            noun_data = {
                "fin": fin_word,
                "eng": item["eng"],
                "inflections": {}
            }
            # Generate all cases and numbers
            for case_name in NOUN_CASES.keys():
                for num_name in NOUN_NUMBERS.keys():
                    key = f"{case_name} {num_name}"
                    tag = get_noun_tag(case_name, num_name)
                    noun_data["inflections"][key] = generate_forms(fin_word, tag)
            nouns.append(noun_data)
            
        elif cat == "V":
            verb_data = {
                "fin": fin_word,
                "eng": item["eng"],
                "verb_type": classify_verb_type(fin_word),
                "inflections": {},
                "participles": {}
            }
            for tense_name in VERB_TENSES_MOODS.keys():
                for person_name in VERB_PERSONS.keys():
                    key = f"{tense_name}, {person_name}"
                    tag = get_verb_tag(tense_name, person_name)
                    verb_data["inflections"][key] = generate_forms(fin_word, tag)
            for prc_name in VERB_PARTICIPLES.keys():
                for case_name in NOUN_CASES.keys():
                    for num_name in NOUN_NUMBERS.keys():
                        key = f"{prc_name}, {case_name} {num_name}"
                        tag = get_participle_tag(prc_name, case_name, num_name)
                        verb_data["participles"][key] = generate_forms(fin_word, tag)
            verbs.append(verb_data)
        else:
            skipped += 1
            
    final_cache = {
        "nouns": nouns,
        "verbs": verbs
    }
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_cache, f, ensure_ascii=False, indent=2)
        
    console.print(f"\n[bold green]Compilation Complete![/bold green]")
    console.print(f"Saved to {output_filepath}")
    console.print(f"- Nouns compiled: {len(nouns)}")
    console.print(f"- Verbs compiled: {len(verbs)}")
    console.print(f"- Skipped (invalid/unknown): {skipped}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_cache(sys.argv[1])
    else:
        # Default fallback
        build_cache("book_of_mormon_complete.csv")
