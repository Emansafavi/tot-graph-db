import argparse
from pathlib import Path

from . import build_data
from .build_data import (
    TAXONOMY_PATH,
    RECORDS_DIR,
    load_json,
    write_json,
    validate_record,
    load_records,
    validate_taxonomy_values,
)


def ingest_record(input_path: Path, overwrite: bool = False) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input record file not found: {input_path}")

    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(
            f"Missing taxonomy file: {TAXONOMY_PATH}. "
            "Create or restore it before ingesting new records."
        )

    raw_record = load_json(input_path)
    record = validate_record(raw_record)

    taxonomy = load_json(TAXONOMY_PATH)
    existing_records = load_records()

    combined_records = existing_records + [record]
    validate_taxonomy_values(combined_records, taxonomy)

    record_id = record.get("id")
    if not record_id:
        raise ValueError("Record must contain a non-empty 'id' field")

    output_path = RECORDS_DIR / f"{record_id}.json"
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Record file already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(output_path, record)

    build_data.main()

    print(f"Ingested record '{record_id}' from {input_path}")
    print(f"Wrote normalized record to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest a single paper record JSON (e.g. produced by an LLM) into "
            "the records/ directory and rebuild graph data."
        )
    )
    parser.add_argument(
        "record_path",
        type=str,
        help="Path to the input JSON file for a single paper record.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing record file with the same id.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.record_path)
    ingest_record(input_path, overwrite=args.overwrite)


if __name__ == "__main__":
    main()

