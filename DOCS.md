# DOCS.md — harness

## approval.printer(value, name)

Writes a text value to a golden master received file.

- Parameters:
  - `value`: `str`. The text content to write.
  - `name`: `str`. The base name used to derive the file path `tests/approval/<name>.received.txt`.
- Returns: `None`.
- Notes: Creates the `tests/approval/` directory if it does not exist.

## approval.reject(name)

Removes a golden master received file.

- Parameters:
  - `name`: `str`. The base name used to derive the file path `tests/approval/<name>.received.txt`.
- Returns: `None`.
- Notes: Does not raise an error if the file does not exist (`missing_ok`).

## approval.approve(name)

Promotes a received file to the approved golden master.

- Parameters:
  - `name`: `str`. The base name. Renames `tests/approval/<name>.received.txt` to `tests/approval/<name>.approved.txt`.
- Returns: `None`.
- Errors: Raises `FileNotFoundError` if the received file does not exist.

## approval.review(name)

Returns a unified diff between the approved and received golden master files.

- Parameters:
  - `name`: `str`. The base name. Reads `tests/approval/<name>.approved.txt` and `tests/approval/<name>.received.txt`.
- Returns: `str`. A unified diff string with `--- approved` and `+++ received` headers.
- Errors: Raises `FileNotFoundError` if either file does not exist.

## harness.version()

Writes the current harness package version to the received file `tests/approval/version.received.txt`.

- Parameters: None.
- Returns: `None`.

## approval(name) (pytest fixture)

Compares a received golden master file against its approved counterpart in `tests/approval/`.

- Parameters:
  - `name`: `str`. The base name. Compares `tests/approval/<name>.approved.txt` with `tests/approval/<name>.received.txt`.
- Behavior:
  - First run (no approved file exists): promotes received to approved.
  - Match: removes the received file silently.
  - Mismatch: fails the test with a unified diff.
  - Received file missing: fails the test with a descriptive message.
