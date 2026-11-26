#!/usr/bin/env python3
"""Regression tests for the airport-codes CSV checker. Fixtures only."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_airport_codes as checker  # noqa: E402

HEADER = ",".join(checker.EXPECTED_HEADER)


def write_bytes(contents: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    with handle:
        handle.write(contents)
    return Path(handle.name)


def write_csv(contents: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".csv",
        delete=False,
    )
    with handle:
        handle.write(contents)
    return Path(handle.name)


def valid_row(**overrides: str) -> str:
    fields = {
        "ident": "EGLL",
        "type": "large_airport",
        "name": "London Heathrow Airport",
        "elevation_ft": "83",
        "continent": "EU",
        "iso_country": "GB",
        "iso_region": "GB-ENG",
        "municipality": "London",
        "icao_code": "EGLL",
        "iata_code": "LHR",
        "gps_code": "EGLL",
        "local_code": "",
        "coordinates": "51.470748, -0.459909",
    }
    fields.update(overrides)
    rendered = []
    for column in checker.EXPECTED_HEADER:
        value = fields[column]
        if any(character in value for character in ",\"\n"):
            value = '"' + value.replace('"', '""') + '"'
        rendered.append(value)
    return ",".join(rendered)


class ValidateAirportCodesTest(unittest.TestCase):
    def test_accepts_a_well_formed_file(self) -> None:
        path = write_csv(HEADER + "\n" + valid_row() + "\n")
        self.assertEqual(checker.validate(path), [])

    def test_accepts_boundary_coordinates(self) -> None:
        path = write_csv(
            HEADER
            + "\n"
            + valid_row(ident="N", coordinates="90, 180")
            + "\n"
            + valid_row(ident="S", coordinates="-90, -180")
            + "\n"
        )
        self.assertEqual(checker.validate(path), [])

    def test_rejects_a_header_that_is_not_the_ourairports_contract(self) -> None:
        path = write_csv("ident,name\nEGLL,Heathrow\n")
        problems = checker.validate(path)
        self.assertTrue(any(problem.startswith("row 1:") for problem in problems))

    def test_reports_the_record_number_of_a_short_row(self) -> None:
        path = write_csv(HEADER + "\n" + valid_row() + "\nEGLL,heliport\n")
        self.assertEqual(
            checker.validate(path),
            ["row 3: expected 13 fields, found 2"],
        )

    def test_unquoted_coordinate_comma_is_reported_as_the_wrong_width(self) -> None:
        bare = valid_row().replace('"51.470748, -0.459909"', "51.470748, -0.459909")
        path = write_csv(HEADER + "\n" + bare + "\n")
        self.assertEqual(
            checker.validate(path),
            ["row 2: expected 13 fields, found 14"],
        )

    def test_quoted_coordinate_comma_still_counts_as_one_field(self) -> None:
        path = write_csv(HEADER + "\n" + valid_row() + "\n")
        self.assertEqual(checker.validate(path), [])

    def test_reports_latitude_and_longitude_that_fall_outside_range(self) -> None:
        path = write_csv(
            HEADER
            + "\n"
            + valid_row(ident="BADLAT", coordinates="91, 0")
            + "\n"
            + valid_row(ident="BADLON", coordinates="0, 181")
            + "\n"
        )
        self.assertEqual(
            checker.validate(path),
            [
                "row 2: latitude 91 is outside [-90, 90]",
                "row 3: longitude 181 is outside [-180, 180]",
            ],
        )

    def test_reports_coordinates_that_do_not_parse_as_a_pair(self) -> None:
        path = write_csv(
            HEADER + "\n" + valid_row(coordinates="not-a-pair") + "\n"
        )
        self.assertEqual(
            checker.validate(path),
            ["row 2: coordinates must be 'lat, lon'"],
        )

    def test_unterminated_quote_is_reported_with_its_record_number(self) -> None:
        broken = valid_row().replace(
            '"51.470748, -0.459909"',
            '"51.470748, -0.459909',
        )
        path = write_csv(HEADER + "\n" + valid_row() + "\n" + broken + "\n")
        self.assertEqual(
            checker.validate(path),
            ["row 3: invalid CSV (unexpected end of data)"],
        )

    def test_unterminated_quote_in_the_header_is_row_one(self) -> None:
        path = write_csv('"ident,type\n')
        self.assertEqual(
            checker.validate(path),
            ["row 1: invalid CSV (unexpected end of data)"],
        )

    def test_invalid_utf8_in_a_later_record_names_that_record(self) -> None:
        prefix = (HEADER + "\n" + valid_row() + "\n").encode("utf-8")
        broken = (
            b"BAD,large_airport,Lon\xffdon,83,EU,GB,GB-ENG,London,"
            b"EGLL,LHR,EGLL,,\"51.47, -0.45\"\n"
        )
        path = write_bytes(prefix + broken)
        self.assertEqual(
            checker.validate(path),
            ["row 3: file is not valid UTF-8"],
        )

    def test_invalid_utf8_inside_a_quoted_field_names_that_record(self) -> None:
        prefix = (HEADER + "\n" + valid_row() + "\n").encode("utf-8")
        broken = (
            b"BAD,large_airport,\"Lon\xffdon\",83,EU,GB,GB-ENG,London,"
            b"EGLL,LHR,EGLL,,\"51.47, -0.45\"\n"
        )
        path = write_bytes(prefix + broken)
        self.assertEqual(
            checker.validate(path),
            ["row 3: file is not valid UTF-8"],
        )

    def test_invalid_utf8_at_the_start_is_row_one(self) -> None:
        path = write_bytes(b"\xff" + HEADER.encode("utf-8") + b"\n")
        self.assertEqual(
            checker.validate(path),
            ["row 1: file is not valid UTF-8"],
        )

    def test_empty_file_is_row_one(self) -> None:
        path = write_csv("")
        self.assertEqual(checker.validate(path), ["row 1: file is empty"])

    def test_main_exits_non_zero_and_prints_row_numbers(self) -> None:
        path = write_csv(HEADER + "\n" + valid_row(coordinates="0, 200") + "\n")
        from io import StringIO

        stdout = StringIO()
        original = sys.stdout
        sys.stdout = stdout
        try:
            code = checker.main(["validate_airport_codes.py", str(path)])
        finally:
            sys.stdout = original
        self.assertEqual(code, 1)
        self.assertIn("row 2: longitude 200 is outside [-180, 180]", stdout.getvalue())

    def test_main_accepts_the_repository_csv(self) -> None:
        from io import StringIO

        original = sys.stdout
        sys.stdout = StringIO()
        try:
            code = checker.main(
                ["validate_airport_codes.py", str(ROOT / "airport-codes.csv")]
            )
        finally:
            sys.stdout = original
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
