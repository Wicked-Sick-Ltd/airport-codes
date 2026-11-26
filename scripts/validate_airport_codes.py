#!/usr/bin/env python3
"""Check airport-codes.csv against the OurAirports column contract.

The checker is deliberately small and uses only the Python standard library.
It reports 1-based CSV record numbers (the header is row 1). A quoted field
that contains a newline still counts as one record, so the number matches a
spreadsheet row rather than a raw file line.
"""

from __future__ import annotations

import csv
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


def validate(path: Path) -> list[str]:
    """Return one message per problem. An empty list means the file passed."""
    problems: list[str] = []
    try:
        handle = path.open(newline="", encoding="utf-8")
    except OSError as exc:
        return [f"could not read {path}: {exc.strerror or exc}"]

    with handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return ["row 1: file is empty"]
        except UnicodeDecodeError:
            return [f"{path} is not valid UTF-8"]

        if header != EXPECTED_HEADER:
            problems.append(
                "row 1: header must be exactly "
                + ",".join(EXPECTED_HEADER)
            )

        for row_number, row in enumerate(reader, start=2):
            width = len(row)
            if width != EXPECTED_WIDTH:
                problems.append(
                    f"row {row_number}: expected {EXPECTED_WIDTH} fields, found {width}"
                )
                continue
            message = parse_coordinates(row[COORDINATES_INDEX])
            if message:
                problems.append(f"row {row_number}: {message}")
    return problems


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
