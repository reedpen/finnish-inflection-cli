import random
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from src.nlp.engine import inflect_noun, inflect_verb, inflect_participle
from src.data.vocab import get_nouns_list, get_verbs_list, get_verbs_by_type

console = Console()
drill_history = InMemoryHistory()
session = PromptSession(history=drill_history)
TOGGLE_VERB_TYPE_FILTER = "__TOGGLE_VERB_TYPE_FILTER__"

def get_hint(hint_level: int, last_attempt: str, answers: list[str]) -> str:
    """Returns a progressive hint based on how many times the user has asked."""
    answer = answers[0]

    if last_attempt:
        best_answer = answers[0]
        best_prefix_len = 0
        for a in answers:
            target = a.lower()
            prefix_len = 0
            for c1, c2 in zip(last_attempt.lower(), target):
                if c1 == c2:
                    prefix_len += 1
                else:
                    break
            if prefix_len > best_prefix_len:
                best_prefix_len = prefix_len
                best_answer = a
        if len(last_attempt) > best_prefix_len:
            return f"'{last_attempt[best_prefix_len]}' at position {best_prefix_len + 1} is wrong"
        answer = best_answer

    reveal_count = min(hint_level, len(answer))
    revealed = answer[:reveal_count]
    remaining = len(answer) - reveal_count
    return f"{revealed}{'_' * remaining}  ({len(answer)} letters)"

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

    answers_lower = {a.lower() for a in answers}
    hint_level = 0
    last_attempt = ""
    while True:
        try:
            user_input = session.prompt("Answer ('h' hint, Enter skip, 'q' quit, 't' toggle type filter): ")
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            if user_input == 'q':
                return False, ""
            if user_input == 't':
                return True, TOGGLE_VERB_TYPE_FILTER
            if user_input == 's' or user_input == '':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"
            if user_input == 'h':
                hint_level += 1
                console.print(f"[yellow]  Hint: {get_hint(hint_level, last_attempt, answers)}[/yellow]")
                continue

            if user_input in answers_lower:
                return True, "[bold green]Correct![/bold green] 🎉"

            last_attempt = user_input
            console.print("[red]  Incorrect, try again.[/red]")
        except (KeyboardInterrupt, EOFError):
            return False, ""

def run_verb_drill(tenses: list[str], persons: list[str], verb_types: list[int] | None = None):
    """Runs a single round of the verb drill."""
    vocab = get_verbs_by_type(verb_types) if verb_types else get_verbs_list()
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

    answers_lower = {a.lower() for a in answers}
    hint_level = 0
    last_attempt = ""
    while True:
        try:
            user_input = session.prompt("Answer ('h' hint, Enter skip, 'q' quit): ")
            if user_input is None:
                return False, ""
            
            user_input = user_input.strip().lower()
            if user_input == 'q':
                return False, ""
            if user_input == 's' or user_input == '':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"
            if user_input == 'h':
                hint_level += 1
                console.print(f"[yellow]  Hint: {get_hint(hint_level, last_attempt, answers)}[/yellow]")
                continue

            if user_input in answers_lower:
                return True, "[bold green]Correct![/bold green] 🎉"

            last_attempt = user_input
            console.print("[red]  Incorrect, try again.[/red]")
        except (KeyboardInterrupt, EOFError):
            return False, ""

def run_participle_drill(participles: list[str], cases: list[str], numbers: list[str]):
    """Runs a single round of the participle drill."""
    vocab = get_verbs_list()
    if not vocab:
        console.print("[red]No Verb vocabulary available![/red]")
        return False, ""

    max_retries = 10
    answers = []
    for _ in range(max_retries):
        participle = random.choice(participles)
        case = random.choice(cases)
        number = random.choice(numbers)
        word_obj = random.choice(vocab)

        fin_word = word_obj['fin']
        lemma = word_obj.get('lemma', fin_word)
        eng_word = word_obj['eng']

        answers = inflect_participle(lemma, participle, case, number)
        if answers:
            break

    if not answers:
        return True, "[red]Failed to generate participle for several verbs.[/red]"

    console.print(f"\n[bold blue]Verb:[/bold blue] {fin_word} ({eng_word})")
    console.print(f"[bold blue]Target:[/bold blue] {participle}, {case} {number}")

    answers_lower = {a.lower() for a in answers}
    hint_level = 0
    last_attempt = ""
    while True:
        try:
            user_input = session.prompt("Answer ('h' hint, Enter skip, 'q' quit): ")
            if user_input is None:
                return False, ""

            user_input = user_input.strip().lower()
            if user_input == 'q':
                return False, ""
            if user_input == 's' or user_input == '':
                return True, f"The correct form(s): [bold green]{', '.join(answers)}[/bold green]"
            if user_input == 'h':
                hint_level += 1
                console.print(f"[yellow]  Hint: {get_hint(hint_level, last_attempt, answers)}[/yellow]")
                continue

            if user_input in answers_lower:
                return True, "[bold green]Correct![/bold green] 🎉"

            last_attempt = user_input
            console.print("[red]  Incorrect, try again.[/red]")
        except (KeyboardInterrupt, EOFError):
            return False, ""
