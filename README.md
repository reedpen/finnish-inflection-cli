# Finnish Inflection CLI

A command-line tool for drilling Finnish noun and verb inflections on the fly using `uralicNLP`.

## Features
- Practice **Nouns** (various cases and numbers)
- Practice **Verbs** (various tenses, moods, and persons)
- Interactive terminal UI using `rich` and `InquirerPy`.
- Generates all morphological inflections dynamically.
- Built-in vocabulary powered by the Book of Mormon dataset.

## Installation

This project uses `uv` for lightning-fast package management.

```bash
# Clone the repository
git clone <url>
cd finnish-inflection-cli

# Initialize the environment and install dependencies
uv sync
```

## Usage

Start the interactive drill:

```bash
uv run python src/main.py
```

Follow the on-screen prompts to select whether you want to practice nouns or verbs, and specifically which inflections you want generated in your practice pool.

## Running Tests
To run the NLP engine tests:
```bash
uv run pytest
```
