import os
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from rich.console import Console
from src.nlp.tags import NOUN_CASES, NOUN_NUMBERS, VERB_TENSES_MOODS, VERB_PERSONS, VERB_PARTICIPLES, VERB_TYPES
from src.ui.drill import run_noun_drill, run_verb_drill, run_participle_drill

console = Console()

ALL_SENTINEL = "__ALL__"

def checkbox_with_all(message: str, options: list[str]) -> list[str] | None:
    """Checkbox prompt with an 'All' shortcut at the top."""
    choices = [
        {"name": "All", "value": ALL_SENTINEL},
        Separator("─" * 20),
        *[{"name": k, "value": k} for k in options],
    ]
    result = inquirer.checkbox(
        message=message,
        choices=choices,
        validate=lambda r: len(r) > 0,
        invalid_message="Minimum 1 selection",
    ).execute()
    if result is None:
        return None
    if ALL_SENTINEL in result:
        return list(options)
    return result

def run_menu():
    while True:
        os.system("clear || cls")
        console.print("[bold blue]==============================[/bold blue]")
        console.print("[bold cyan]   Finnish Inflection Drill   [/bold cyan]")
        console.print("[bold blue]==============================[/bold blue]\n")
        
        choice = inquirer.select(
            message="Choose a drill:",
            choices=[
                "Practice Nouns",
                "Practice Verbs",
                "Practice Participles",
                "Exit"
            ]
        ).execute()

        if choice is None or choice == "Exit":
            console.print("[yellow]Näkemiin![/yellow]")
            break

        if choice == "Practice Nouns":
            setup_noun_drill()
        elif choice == "Practice Verbs":
            setup_verb_drill()
        elif choice == "Practice Participles":
            setup_participle_drill()

def setup_noun_drill():
    cases = checkbox_with_all("Select noun cases to practice:", list(NOUN_CASES.keys()))
    if cases is None: return

    numbers = checkbox_with_all("Select numbers:", list(NOUN_NUMBERS.keys()))
    if numbers is None: return
    
    feedback = ""
    while True:
        try:
            os.system("clear || cls")
            console.print(f"[bold magenta]--- Starting Noun Drill ---[/bold magenta]")
            console.print("(Type 'quit' or press Ctrl+C to return to menu)\n")
            
            if feedback:
                console.print(feedback + "\n")
                
            should_continue, feedback = run_noun_drill(cases, numbers)
            if not should_continue:
                break
        except Exception as e:
            console.print(f"[red]Encountered error in loop: {e}[/red]")
            import traceback
            traceback.print_exc()
            console.input("\nPress Enter to return to main menu...")
            break

def setup_verb_drill():
    verb_type_labels = checkbox_with_all("Select verb types:", list(VERB_TYPES.keys()))
    if verb_type_labels is None: return

    tenses = checkbox_with_all("Select tenses and moods:", list(VERB_TENSES_MOODS.keys()))
    if tenses is None: return

    persons = checkbox_with_all("Select persons:", list(VERB_PERSONS.keys()))
    if persons is None: return

    verb_types = [VERB_TYPES[label] for label in verb_type_labels]
    
    feedback = ""
    while True:
        try:
            os.system("clear || cls")
            console.print(f"[bold magenta]--- Starting Verb Drill ---[/bold magenta]")
            console.print("(Type 'quit' or press Ctrl+C to return to menu)\n")
            
            if feedback:
                console.print(feedback + "\n")
                
            should_continue, feedback = run_verb_drill(tenses, persons, verb_types)
            if not should_continue:
                break
        except Exception as e:
            console.print(f"[red]Encountered error in loop: {e}[/red]")
            import traceback
            traceback.print_exc()
            console.input("\nPress Enter to return to main menu...")
            break

def setup_participle_drill():
    participles = checkbox_with_all("Select participle types to practice:", list(VERB_PARTICIPLES.keys()))
    if participles is None: return

    cases = checkbox_with_all("Select cases to decline participles in:", list(NOUN_CASES.keys()))
    if cases is None: return

    numbers = checkbox_with_all("Select numbers:", list(NOUN_NUMBERS.keys()))
    if numbers is None: return

    feedback = ""
    while True:
        try:
            os.system("clear || cls")
            console.print(f"[bold magenta]--- Starting Participle Drill ---[/bold magenta]")
            console.print("(Type 'quit' or press Ctrl+C to return to menu)\n")

            if feedback:
                console.print(feedback + "\n")

            should_continue, feedback = run_participle_drill(participles, cases, numbers)
            if not should_continue:
                break
        except Exception as e:
            console.print(f"[red]Encountered error in loop: {e}[/red]")
            import traceback
            traceback.print_exc()
            console.input("\nPress Enter to return to main menu...")
            break
