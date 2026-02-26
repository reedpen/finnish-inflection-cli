import random
from InquirerPy import inquirer
from rich.console import Console
from src.nlp.engine import inflect_noun, inflect_verb
from src.data.vocab import get_nouns_list, get_verbs_list

console = Console()

def run_noun_drill(cases: list[str], numbers: list[str]):
    """Runs a single round of the noun drill."""
    vocab = get_nouns_list()
    if not vocab:
        console.print("[red]No Noun vocabulary available![/red]")
        return False, ""
        
    # Attempt to find a valid word/case combo that generates results
    max_retries = 10
    answers = []
    for _ in range(max_retries):
        case = random.choice(cases)
        number = random.choice(numbers)
        word_obj = random.choice(vocab)
        
        fin_word = word_obj['fin']
        lemma = word_obj.get('lemma', fin_word)
        pos = word_obj.get('pos', 'N')
        eng_word = word_obj['eng']
        
        # Generate correct answer
        answers = inflect_noun(lemma, case, number, pos)
        if answers:
            break
            
    if not answers:
        return True, "[red]Failed to generate inflection for several words. Try different cases?[/red]"
        
    console.print(f"\n[bold blue]Word:[/bold blue] {fin_word} ({eng_word})")
    console.print(f"[bold blue]Target:[/bold blue] {case} {number}")
    
    while True:
        try:
            user_input = inquirer.text(message="Inflection (type 's' to skip, 'q' to quit):").execute()
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            
            if user_input == 'q':
                return False, ""
                
            if user_input == 's':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"

            if user_input in [a.lower() for a in answers]:
                return True, "[bold green]Correct![/bold green] 🎉"
            else:
                # No "incorrect" message, just let them try again
                pass
                
        except KeyboardInterrupt:
            return False, ""

def run_verb_drill(tenses: list[str], persons: list[str]):
    """Runs a single round of the verb drill."""
    vocab = get_verbs_list()
    if not vocab:
        console.print("[red]No Verb vocabulary available![/red]")
        return False, ""
        
    # Attempt to find a valid word/tense combo that generates results
    max_retries = 10
    answers = []
    for _ in range(max_retries):
        tense = random.choice(tenses)
        person = random.choice(persons)
        word_obj = random.choice(vocab)
        
        fin_word = word_obj['fin']
        lemma = word_obj.get('lemma', fin_word)
        eng_word = word_obj['eng']
        
        answers = inflect_verb(lemma, tense, person)
        if answers:
            break
            
    if not answers:
        return True, "[red]Failed to generate inflection for several verbs. Try different tenses?[/red]"
        
    console.print(f"\n[bold blue]Verb:[/bold blue] {fin_word} ({eng_word})")
    console.print(f"[bold blue]Target:[/bold blue] {tense}, {person}")
    
    while True:
        try:
            user_input = inquirer.text(message="Inflection (type 's' to skip, 'q' to quit):").execute()
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            
            if user_input == 'q':
                return False, ""

            if user_input == 's':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"
                
            if user_input in [a.lower() for a in answers]:
                return True, "[bold green]Correct![/bold green] 🎉"
            else:
                # No "incorrect" message, just let them try again
                pass
                
        except KeyboardInterrupt:
            return False, ""
