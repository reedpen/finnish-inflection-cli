import random
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from src.nlp.engine import inflect_noun, inflect_verb
from src.data.vocab import get_nouns_list, get_verbs_list

console = Console()
drill_history = InMemoryHistory()
session = PromptSession(history=drill_history)

def get_hint_text(current_input: str, answers: list[str]) -> str:
    """Calculates a hint based on the longest common prefix among possible answers."""
    if not current_input:
        return f"Hint: Starts with '{answers[0][0]}'"
    
    current = current_input.lower()
    best_answer = answers[0]
    best_prefix_len = 0
    
    # Find which correct answer the user is closest to
    for a in answers:
        target = a.lower()
        prefix_len = 0
        for c1, c2 in zip(current, target):
            if c1 == c2:
                prefix_len += 1
            else:
                break
        if prefix_len > best_prefix_len:
            best_prefix_len = prefix_len
            best_answer = a
            
    if len(current) > best_prefix_len:
        return f"Hint: Remove '{current[best_prefix_len]}'"
    elif best_prefix_len < len(best_answer):
        return f"Hint: Next is '{best_answer[best_prefix_len]}'"
    else:
        return "Hint: Correct! Press Enter."

def run_noun_drill(cases: list[str], numbers: list[str]):
    """Runs a single round of the noun drill."""
    vocab = get_nouns_list()
    if not vocab:
        console.print("[red]No Noun vocabulary available![/red]")
        return False, ""
        
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
        
        answers = inflect_noun(lemma, case, number, pos)
        if answers:
            break
            
    if not answers:
        return True, "[red]Failed to generate inflection for several words.[/red]"
        
    console.print(f"\n[bold blue]Word:[/bold blue] {fin_word} ({eng_word})")
    console.print(f"[bold blue]Target:[/bold blue] {case} {number}")
    
    def bottom_toolbar():
        return get_hint_text(session.default_buffer.text, answers)

    while True:
        try:
            user_input = session.prompt(
                "Inflection (Enter to skip, 'q' to quit): ",
                bottom_toolbar=bottom_toolbar,
                mouse_support=True
            )
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            if user_input == 'q':
                return False, ""
            if user_input == 's' or user_input == '':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"

            if user_input in [a.lower() for a in answers]:
                return True, "[bold green]Correct![/bold green] 🎉"
        except (KeyboardInterrupt, EOFError):
            return False, ""

def run_verb_drill(tenses: list[str], persons: list[str]):
    """Runs a single round of the verb drill."""
    vocab = get_verbs_list()
    if not vocab:
        console.print("[red]No Verb vocabulary available![/red]")
        return False, ""
        
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
        return True, "[red]Failed to generate inflection for several verbs.[/red]"
        
    console.print(f"\n[bold blue]Verb:[/bold blue] {fin_word} ({eng_word})")
    console.print(f"[bold blue]Target:[/bold blue] {tense}, {person}")
    
    def bottom_toolbar():
        return get_hint_text(session.default_buffer.text, answers)

    while True:
        try:
            user_input = session.prompt(
                "Inflection (Enter to skip, 'q' to quit): ",
                bottom_toolbar=bottom_toolbar,
                mouse_support=True
            )
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            if user_input == 'q':
                return False, ""
            if user_input == 's' or user_input == '':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"
                
            if user_input in [a.lower() for a in answers]:
                return True, "[bold green]Correct![/bold green] 🎉"
        except (KeyboardInterrupt, EOFError):
            return False, ""
