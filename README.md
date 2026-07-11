# Finnish Inflection CLI

An interactive command-line tool for practicing Finnish noun, adjective, and
verb inflections. It uses UralicNLP/Omorfi to generate answers and includes a
small reviewed starter vocabulary.

## Install

Python 3.11 or newer is required. From a source checkout with `pip`:

```bash
python -m pip install .
finnish-drill
```

You can also install a built wheel with
`python -m pip install dist/finnish_inflection_cli-*.whl`.

From a source checkout with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run finnish-drill
```

For a user-level uv installation that can be upgraded or removed independently:

```bash
uv tool install .
uv tool upgrade finnish-inflection-cli
uv tool uninstall finnish-inflection-cli
```

Useful package commands:

```bash
python -m pip install --upgrade .
python -m pip uninstall finnish-inflection-cli
finnish-drill --help
finnish-drill --version
```

On first use, UralicNLP may download the Finnish morphology model. This can
take several minutes. If setup fails, check the network connection, available
disk space, and write permissions in the UralicNLP data directory, then retry.

## Practice

Run `finnish-drill` and choose a noun/adjective or verb drill. The menus let you
focus the practice pool by grammatical form. On-screen commands provide hints,
skip a question, go back, or end the session.

## Custom vocabulary

Imports accept UTF-8 files in either format:

- Semicolon-delimited CSV with the exact headers `Front;Back`.
- Text containing one `Finnish,English` pair per line.

Ready-to-copy files are in [`examples/vocabulary.csv`](examples/vocabulary.csv)
and [`examples/vocabulary.txt`](examples/vocabulary.txt).

Preview and install a named set, then select it:

```bash
finnish-drill vocab import lesson-1 examples/vocabulary.csv
finnish-drill vocab list
finnish-drill vocab select lesson-1
finnish-drill vocab select default
finnish-drill vocab remove lesson-1
```

The same workflow is available from **Manage vocabulary** in the interactive
main menu, including preview, replacement confirmation, selection, and removal.

Import validates headers, UTF-8 encoding, required Finnish and English values,
duplicate lemmas, morphology analyses, verb types, and the versioned document
schema. It shows accepted, corrected, ambiguous, excluded, and rejected totals
before asking to install. `--replace` atomically replaces a named set; `--yes`
is intended for reviewed automation. A cancelled or failed import does not
alter existing sets.

Ambiguous words are rejected until reviewed. Supply `--overrides review.json`
where each key is a Finnish display form. Map it to an explicit lemma and part
of speech (`N`, `A`, or `V`), or to `null` to exclude it:

```json
{
  "kuusi": {"lemma": "kuusi", "pos": "N"},
  "pois": null
}
```

Named sets are stored under the operating system's standard user-data
directory. Their JSON files use `schema_version`, a source SHA-256 fingerprint,
metadata, and uniformly validated entries.

## Default vocabulary and data provenance

The canonical starter list is `src/data/default_vocab.csv`. Its Finnish display
form, English hint, reviewed lemma, part of speech, and verb type are transformed
deterministically into packaged `src/data/default_vocab.json`. The checked-in
overrides resolve five analyzer ambiguities using the reviewed lemma and part of
speech. The review report records those decisions, source fingerprints, and a
successful real-model generated-form check. Verify the complete chain with:

```bash
python -m src.scripts.build_default_vocab --check
```

Rerun the morphology quality gate after changing the canonical vocabulary:

```bash
python -m src.scripts.build_default_vocab --validate-model
```

That deterministic check validates source and override hashes and rejects stale
review artifacts, duplicates, empty values, unsupported parts of speech, and
recorded analysis/form failures. To additionally load the real Finnish model
and verify every reviewed lemma plus a representative generated form, run:

```bash
python -m src.scripts.build_default_vocab --check --validate-model
```

Model validation is opt-in because it requires the downloaded UralicNLP data.
Its detailed result is printed; the deterministic checked-in report records the
opt-in status and exact command without embedding machine-specific results.

The result is loaded through Python package resources and does not depend on the
current working directory. The quality gate rejects partial records, unsupported
parts of speech, duplicates, empty translations, and verbs without a type from
1 through 6.

The repository also contains a historical `book_of_mormon_complete.csv` and an
old cache. No source URL or redistribution license for that dataset is recorded
in the repository history, so it is **not packaged as the default vocabulary**.
Its provenance and redistribution rights must be established by the repository
owner before publishing it. The software and maintainer-authored starter list
are currently all-rights-reserved under `LicenseRef-Proprietary`; see `LICENSE`.

To rebuild a reviewed source, use explicit overrides/exclusions. The build
writes a review report and refuses to publish when rejected entries remain:

```bash
uv run python -m src.scripts.build_cache words.csv \
  --overrides review.json --output reviewed.json --report review-report.json
```

## Development

The normal test suite uses injected morphology adapters and does not download a
model:

```bash
uv run pytest
```

Tests marked `integration` use the real Finnish model and can be run explicitly
after installing it:

```bash
uv run pytest -m integration
```
