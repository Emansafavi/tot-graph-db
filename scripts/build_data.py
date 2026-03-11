import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_DIR = BASE_DIR / "records"
DATA_DIR = BASE_DIR / "data"
TAXONOMY_PATH = DATA_DIR / "taxonomy.json"
PAPERS_OUT = DATA_DIR / "papers.json"
RELATIONS_OUT = DATA_DIR / "relations.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_list_field(record, field_name):
    value = record.get(field_name, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{record.get('id', '<unknown>')}: field '{field_name}' must be a list")
    return value


def validate_record(record):
    required_fields = ["id", "title"]
    for field in required_fields:
        if not record.get(field):
            raise ValueError(f"Missing required field '{field}' in record")

    record["authors"] = validate_list_field(record, "authors")
    record["key_concepts"] = validate_list_field(record, "key_concepts")
    record["themes"] = validate_list_field(record, "themes")
    record["methods"] = validate_list_field(record, "methods")
    record["tensions"] = validate_list_field(record, "tensions")
    record["quotes"] = validate_list_field(record, "quotes")

    related = record.get("related", [])
    if related is None:
        related = []
    if not isinstance(related, list):
        raise ValueError(f"{record['id']}: field 'related' must be a list")

    normalized_related = []
    for item in related:
        if isinstance(item, str):
            normalized_related.append({
                "target": item,
                "type": "related",
                "reason": ""
            })
        elif isinstance(item, dict):
            target = item.get("target")
            if not target:
                raise ValueError(f"{record['id']}: every related item must have a 'target'")
            normalized_related.append({
                "target": target,
                "type": item.get("type", "related"),
                "reason": item.get("reason", "")
            })
        else:
            raise ValueError(f"{record['id']}: invalid item in 'related'")
    record["related"] = normalized_related

    return record


def load_records():
    records = []
    for path in sorted(RECORDS_DIR.glob("*.json")):
        record = load_json(path)
        record = validate_record(record)
        record["_filename"] = path.name
        records.append(record)
    return records


def validate_taxonomy_values(records, taxonomy):
    valid_themes = set(taxonomy.get("themes", {}).keys())
    valid_methods = set(taxonomy.get("methods", {}).keys())
    valid_tensions = set(taxonomy.get("tensions", {}).keys())
    valid_relation_types = set(taxonomy.get("relation_types", {}).keys())

    errors = []

    for record in records:
        for theme in record.get("themes", []):
            if theme not in valid_themes:
                errors.append(f"{record['id']}: unknown theme '{theme}'")

        for method in record.get("methods", []):
            if method not in valid_methods:
                errors.append(f"{record['id']}: unknown method '{method}'")

        for tension in record.get("tensions", []):
            if tension not in valid_tensions:
                errors.append(f"{record['id']}: unknown tension '{tension}'")

        for rel in record.get("related", []):
            if rel["type"] not in valid_relation_types:
                errors.append(f"{record['id']}: unknown relation type '{rel['type']}'")

    if errors:
        raise ValueError("Taxonomy validation failed:\n" + "\n".join(errors))


def build_papers(records, taxonomy):
    built = []

    for record in records:
        primary_theme = record["themes"][0] if record.get("themes") else None
        theme_meta = taxonomy.get("themes", {}).get(primary_theme, {})
        color = theme_meta.get("color", "#888888")

        built.append({
            "id": record["id"],
            "title": record["title"],
            "label": record.get("short_title") or record["title"],
            "authors": record.get("authors", []),
            "year": record.get("year", ""),
            "status": record.get("status", ""),
            "source_type": record.get("source_type", "paper"),
            "pdf_path": record.get("pdf_path", ""),
            "doi": record.get("doi", ""),
            "url": record.get("url", ""),
            "summary": record.get("summary", ""),
            "key_concepts": record.get("key_concepts", []),
            "themes": record.get("themes", []),
            "methods": record.get("methods", []),
            "tensions": record.get("tensions", []),
            "notes": record.get("notes", ""),
            "quotes": record.get("quotes", []),
            "related": record.get("related", []),
            "primary_theme": primary_theme,
            "color": color,
            "filename": record.get("_filename", "")
        })

    return built


def build_relations(records):
    seen = set()
    built = []

    valid_ids = {record["id"] for record in records}

    for record in records:
        source = record["id"]

        for rel in record.get("related", []):
            target = rel["target"]

            if target not in valid_ids:
                print(f"Warning: {source} references missing target '{target}'")
                continue

            edge_key = (source, target, rel["type"])
            reverse_edge_key = (target, source, rel["type"])

            if edge_key in seen or reverse_edge_key in seen:
                continue

            built.append({
                "source": source,
                "target": target,
                "type": rel["type"],
                "reason": rel.get("reason", "")
            })
            seen.add(edge_key)

    return built


def main():
    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(f"Missing taxonomy file: {TAXONOMY_PATH}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)

    taxonomy = load_json(TAXONOMY_PATH)
    records = load_records()

    validate_taxonomy_values(records, taxonomy)

    papers = build_papers(records, taxonomy)
    relations = build_relations(records)

    write_json(PAPERS_OUT, papers)
    write_json(RELATIONS_OUT, relations)

    print(f"Built {len(papers)} papers")
    print(f"Built {len(relations)} relations")
    print(f"Wrote {PAPERS_OUT}")
    print(f"Wrote {RELATIONS_OUT}")


if __name__ == "__main__":
    main()