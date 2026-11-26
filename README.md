Created this whilst matching Cloudflare POPs to their locations.  They seem to use airport codes to identify their POPs. 

CSV contains:
ident, type, name, elevation_ft, continent, iso_country, iso_region, municipality, icao_code, iata_code, gps_code, local_code, coordinates

Accurate as of **March 2026** with **84,971** entries.  We have many airports around the world!

## `type` values

`type` is the OurAirports category for the aerodrome. This file uses the seven values below. The wording follows the [OurAirports map legend](https://ourairports.com/help/).

| `type` | Meaning |
| --- | --- |
| `large_airport` | Land airport with scheduled major airline service, or a major military base. |
| `medium_airport` | Land airport with scheduled regional airline service, or regular general-aviation or military traffic. |
| `small_airport` | Land airport with little or no scheduled service and light general-aviation traffic. |
| `heliport` | Helicopter pad, with no runway for fixed-wing aircraft. |
| `seaplane_base` | Docking or fuelling area for seaplanes, with no facilities for land aircraft. |
| `balloonport` | Area for launching hot-air balloons. |
| `closed` | An airport that is no longer operational. |

The current OurAirports data dictionary spells that last category `closed_airport`. This export stores it as `closed`.

## Joining Cloudflare points of presence

Cloudflare names many points of presence with a three-letter IATA airport code. Join that code to the `iata_code` column. `ident` and `icao_code` on the same row are often the four-letter ICAO code, so the IATA code lives only in `iata_code`. Rows with no IATA assignment leave `iata_code` blank.

Worked example: the London point of presence `LHR` matches the Heathrow row.

| ident | type | name | iso_country | iata_code | coordinates |
| --- | --- | --- | --- | --- | --- |
| EGLL | large_airport | London Heathrow Airport | GB | LHR | 51.470748, -0.459909 |

On this row the join key is `iata_code` (`LHR`). `ident` and `icao_code` are both `EGLL`.

## Checking the file

`scripts/validate_airport_codes.py` checks three things, using only the Python standard library:

- the header is exactly the 13 OurAirports columns above, from `ident` through `coordinates`
- every data row has that same field count (quoted commas, including the comma inside `coordinates`, stay inside one field)
- `coordinates` parses as `lat, lon`, with latitude in [-90, 90] and longitude in [-180, 180]

It prints the 1-based CSV record number of each failing row (the header is row 1) and exits non-zero when anything fails. GitHub Actions runs the same command on pull requests and on pushes to `main`.

```bash
python3 scripts/validate_airport_codes.py airport-codes.csv
```

<!-- repository-guidance:begin -->
## Contributing and agent guidance

- [Contributor guide](CONTRIBUTING.md): development workflow and validation.
- [Agent instructions](AGENTS.md): shared guidance for Codex and other coding agents.
- [Security policy](SECURITY.md): private vulnerability reporting.

## Repository license

MIT licensed; see [LICENSE](LICENSE). Preserve third-party notices.
<!-- repository-guidance:end -->
