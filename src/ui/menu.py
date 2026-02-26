import os
from InquirerPy import inquirer
from rich.console import Console
from src.nlp.tags import NOUN_CASES, NOUN_NUMBERS, VERB_TENSES_MOODS, VERB_PERSONS
from src.ui.drill import run_noun_drill, run_verb_drill

console = Console()

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

def setup_noun_drill():
    cases = inquirer.checkbox(
        message="Select noun cases to practice:",
        choices=[{"name": k, "value": k} for k in NOUN_CASES.keys()],
        validate=lambda result: len(result) > 0,
        invalid_message="Minimum 1 selection"
    ).execute()
    if cases is None: return
    
    numbers = inquirer.checkbox(
        message="Select numbers:",
        choices=[{"name": k, "value": k} for k in NOUN_NUMBERS.keys()],
        validate=lambda result: len(result) > 0,
        invalid_message="Minimum 1 selection"
    ).execute()
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
            console.print(f"[red]Encountered error: {e}[/red]")
            break

def setup_verb_drill():
    tenses = inquirer.checkbox(
        message="Select tenses and moods:",
        choices=[{"name": k, "value": k} for k in VERB_TENSES_MOODS.keys()],
        validate=lambda result: len(result) > 0,
        invalid_message="Minimum 1 selection"
    ).execute()
    if tenses is None: return
    
    persons = inquirer.checkbox(
        message="Select persons:",
        choices=[{"name": k, "value": k} for k in VERB_PERSONS.keys()],
        validate=lambda result: len(result) > 0,
        invalid_message="Minimum 1 selection"
    ).execute()
    if persons is None: return
    
    feedback = ""
    while True:
        try:
            os.system("clear || cls")
            console.print(f"[bold magenta]--- Starting Verb Drill ---[/bold magenta]")
            console.print("(Type 'quit' or press Ctrl+C to return to menu)\n")
            
            if feedback:
                console.print(feedback + "\n")
                
            should_continue, feedback = run_verb_drill(tenses, persons)
            if not should_continue:
                break
        except Exception as e:
            console.print(f"[red]Encountered error: {e}[/red]")
            break
