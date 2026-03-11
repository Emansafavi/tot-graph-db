import argparse
from pathlib import Path
from typing import Dict, List, Tuple

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


def _parse_frontmatter(lines: List[str]) -> Tuple[Dict, int]:
    """
    Very small YAML-like parser for the frontmatter in notes/*.md.

    Supports:
    - key: "value"
    - key: value
    - key:
        - item1
        - item2
    """
    data: Dict = {}
    current_key = None
    i = 0

    # Expect starting '---'
    if not lines or lines[0].strip() != "---":
        raise ValueError("Note is missing starting '---' frontmatter delimiter")

    i += 1
    while i < len(lines):
        line = lines[i].rstrip("\n")
        stripped = line.strip()

        if stripped == "---":
            i += 1
            break

        if not stripped:
            i += 1
            continue

        if stripped.startswith("- ") and current_key:
            # list item for the current key
            item = stripped[2:].strip()
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            data.setdefault(current_key, []).append(item)
            i += 1
            continue

        # New key
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value == "":
                # start of list
                data[key] = []
                current_key = key
            else:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                # try to parse int for simple numeric year fields
                if key == "year":
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                data[key] = value
                current_key = None

        i += 1

    return data, i


def _split_sections(lines: List[str]) -> Dict[str, List[str]]:
    """
    Split markdown body into sections by top-level '# ' headings.
    Returns a dict mapping lowercased section titles to their content lines.
    """
    sections: Dict[str, List[str]] = {}
    current_title = None

    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("# "):
            current_title = stripped[2:].strip().lower()
            sections[current_title] = []
        else:
            if current_title is not None:
                sections[current_title].append(line)

    return sections


def _extract_from_sections(sections: Dict[str, List[str]]) -> Dict:
    summary_lines = sections.get("summary", [])
    key_concept_lines = sections.get("key concepts", [])
    notes_lines = sections.get("notes", [])
    quotes_lines = sections.get("quotes", [])

    summary = "".join(summary_lines).strip()

    key_concepts: List[str] = []
    for line in key_concept_lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if item:
                key_concepts.append(item)

    notes = "".join(notes_lines).strip()

    quotes: List[str] = []
    for line in quotes_lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            item = stripped.lstrip(">").strip()
            if item:
                quotes.append(item)

    return {
        "summary": summary,
        "key_concepts": key_concepts,
        "notes": notes,
        "quotes": quotes,
    }


def note_to_record(path: Path) -> Dict:
    """
    Convert a single markdown note (with frontmatter and sections)
    into a record dict compatible with records/*.json.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    frontmatter, body_start = _parse_frontmatter(lines)
    sections = _split_sections(lines[body_start:])
    derived = _extract_from_sections(sections)

    record: Dict = {}

    # Map simple frontmatter fields
    record["id"] = frontmatter.get("id", "").strip()
    record["title"] = frontmatter.get("title", "").strip()

    # authors, themes, methods, tensions, related as lists (or empty)
    for field in ["authors", "themes", "methods", "tensions", "related"]:
        value = frontmatter.get(field, [])
        if value is None:
            value = []
        record[field] = value

    # year, status, paths and identifiers
    if "year" in frontmatter:
        record["year"] = frontmatter["year"]
    record["status"] = frontmatter.get("status", "").strip()
    record["source_type"] = "paper"
    record["pdf_path"] = frontmatter.get("pdf", "").strip()
    record["doi"] = frontmatter.get("doi", "").strip()
    record["url"] = frontmatter.get("source", "").strip()

    # Derived content from sections
    record.update(derived)

    return record


def ingest_note(note_path: Path, overwrite: bool = False) -> None:
    if not note_path.exists():
        raise FileNotFoundError(f"Note file not found: {note_path}")

    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(
            f"Missing taxonomy file: {TAXONOMY_PATH}. "
            "Create or restore it before ingesting new notes."
        )

    record = note_to_record(note_path)
    record = validate_record(record)

    taxonomy = load_json(TAXONOMY_PATH)
    existing_records = load_records()
    combined_records = existing_records + [record]
    validate_taxonomy_values(combined_records, taxonomy)

    record_id = record.get("id")
    if not record_id:
        raise ValueError("Note frontmatter must contain a non-empty 'id' field")

    output_path = RECORDS_DIR / f"{record_id}.json"
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Record file already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(output_path, record)

    build_data.main()

    print(f"Ingested note '{record_id}' from {note_path}")
    print(f"Wrote normalized record to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest a markdown note (with frontmatter and sections) into "
            "the records/ directory and rebuild graph data."
        )
    )
    parser.add_argument(
        "note_path",
        type=str,
        help="Path to the markdown note file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing record file with the same id.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    note_path = Path(args.note_path)
    ingest_note(note_path, overwrite=args.overwrite)


if __name__ == "__main__":
    main()

