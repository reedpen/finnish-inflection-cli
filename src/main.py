import os
os.environ["INQUIRERPY_MOUSE_SUPPORT"] = "true"

import sys
import io

# Add the root directory to sys.path so 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console

# Redirect stdout temporarily during uralicNLP initialization if needed
console = Console()

def main():
    try:
        # Import inside try block so we can see loading message
        from src.data.vocab import load_book_of_mormon_vocab
        from src.nlp.engine import ensure_model_downloaded
        from src.ui.menu import run_menu
        
        with console.status("[bold green]Loading NLP model & vocabulary...[/bold green]", spinner="dots"):
            ensure_model_downloaded("fin")
            nouns, verbs = load_book_of_mormon_vocab()
            
        console.print(f"[dim]Loaded {len(nouns)} nouns/adjectives and {len(verbs)} verbs.[/dim]")
        print("\n")
        run_menu()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Näkemiin![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
