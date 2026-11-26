# Contributing to airport-codes

## Getting started

Read [README.md](README.md) and [AGENTS.md](AGENTS.md) for project layout and setup. Use the dependency versions and lockfiles already in the repository. Configure local test services and keep credentials outside Git.

## Making changes

Start from the current `main` branch and use a focused topic branch. Preserve unrelated work. Follow existing naming and formatting conventions; update documentation when commands, configuration, or behavior change.

## Validation

- `git diff --check` — check whitespace in documentation and configuration changes.
- `python3 scripts/validate_airport_codes.py airport-codes.csv` — check the CSV header, field counts, and co-ordinates.
- `python3 -m unittest discover -s tests -v` — run the checker tests.

Run the relevant checks before submitting. For documentation-only changes, verify links and commands and run `git diff --check`. Record unavailable dependencies or skipped checks explicitly. Use isolated test data and mock external services where supported.

## Pull requests

Describe the problem and resulting behavior, link relevant issues, and list validation commands and results. Include screenshots for UI changes and explain configuration or migration impacts. Use concise commit subjects consistent with the repository history. Address review findings and required checks before merging; a documentation change does not authorize deployment.

## Security and licensing

Report vulnerabilities using [SECURITY.md](SECURITY.md), not public issues. MIT licensed; see [LICENSE](LICENSE). Preserve third-party notices.
