#!/usr/bin/env python3
"""Check airport-codes.csv against the OurAirports column contract.

The checker is deliberately small and uses only the Python standard library.
It reports 1-based CSV record numbers (the header is row 1). A quoted field
that contains a newline still counts as one record, so the number matches a
spreadsheet row rather than a raw file line.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

EXPECTED_HEADER = [
    "ident",
    "type",
    "name",
    "elevation_ft",
    "continent",
    "iso_country",
    "iso_region",
    "municipality",
    "icao_code",
    "iata_code",
    "gps_code",
    "local_code",
    "coordinates",
]

EXPECTED_WIDTH = len(EXPECTED_HEADER)
COORDINATES_INDEX = EXPECTED_HEADER.index("coordinates")


def parse_coordinates(value: str) -> str | None:
    """Return an error message, or None when value is 'lat, lon' in range."""
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return "coordinates must be 'lat, lon'"
    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return "coordinates must be 'lat, lon'"
    if not -90 <= latitude <= 90:
        return f"latitude {parts[0]} is outside [-90, 90]"
    if not -180 <= longitude <= 180:
        return f"longitude {parts[1]} is outside [-180, 180]"
    return None


def utf8_record_problem(path: Path) -> str | None:
    """Name the CSV record that contains the first invalid UTF-8 byte.

    Decoding through TextIOWrapper is the wrong place to count records: it
    decodes a buffer ahead of the record the parser is on, so the exception
    lands on an earlier row. The byte offset from decoding the whole file
    sits on the record that actually contains the bad byte.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        return f"could not read {path}: {exc.strerror or exc}"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        prefix = data[: exc.start].decode("utf-8")
        if prefix == "":
            return "row 1: file is not valid UTF-8"
        complete = 0
        partial = False
        reader = csv.reader(io.StringIO(prefix), strict=True)
        try:
            for _ in reader:
                complete += 1
        except csv.Error:
            # The offset falls inside a quoted field, so the open record
            # was not counted.
            partial = True
        if partial or prefix.endswith(("\n", "\r")):
            row_number = complete + 1
        else:
            # The offset falls inside an unquoted field. The reader treats
            # end of input as the end of that record and has already counted it.
            row_number = complete
        return f"row {row_number}: file is not valid UTF-8"
    return None


def validate(path: Path) -> list[str]:
    """Return one message per problem. An empty list means the file passed."""
    encoding_problem = utf8_record_problem(path)
    if encoding_problem:
        return [encoding_problem]

    problems: list[str] = []
    try:
        handle = path.open(newline="", encoding="utf-8")
    except OSError as exc:
        return [f"could not read {path}: {exc.strerror or exc}"]

    with handle:
        # strict=True rejects an unterminated quote. The default reader would
        # otherwise accept a broken final field and report the file as valid.
        reader = csv.reader(handle, strict=True)
        header, failure = read_record(reader, 1)
        if failure == "eof":
            return ["row 1: file is empty"]
        if failure:
            return [failure]
        if header != EXPECTED_HEADER:
            problems.append(
                "row 1: header must be exactly "
                + ",".join(EXPECTED_HEADER)
            )

        row_number = 2
        while True:
            row, failure = read_record(reader, row_number)
            if failure == "eof":
                break
            if failure:
                problems.append(failure)
                break
            width = len(row)
            if width != EXPECTED_WIDTH:
                problems.append(
                    f"row {row_number}: expected {EXPECTED_WIDTH} fields, found {width}"
                )
            else:
                message = parse_coordinates(row[COORDINATES_INDEX])
                if message:
                    problems.append(f"row {row_number}: {message}")
            row_number += 1
    return problems


def read_record(reader: csv.reader, row_number: int) -> tuple[list[str] | None, str | None]:
    """Return (row, None), (None, 'eof'), or (None, error message)."""
    try:
        return next(reader), None
    except StopIteration:
        return None, "eof"
    except csv.Error as exc:
        return None, f"row {row_number}: invalid CSV ({exc})"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: validate_airport_codes.py <csv>",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 2
    problems = validate(path)
    if problems:
        print(f"{path}: {len(problems)} problem(s)")
        for problem in problems:
            print(problem)
        return 1
    print(f"{path}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
