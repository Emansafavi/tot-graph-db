## Technologies of Touch Graph (tot-graph-db)

This repository contains a small literature database and graph visualization for the "Technologies of Touch" research project.

### Data model

- `records/` — canonical JSON records for each paper (one file per paper).
- `data/taxonomy.json` — controlled vocabularies for themes, methods, tensions, and relation types.
- `data/papers.json` and `data/relations.json` — generated graph data consumed by the web app.
- `notes/` — Markdown notes created by researchers using the `_template.md` scaffold.

The web app in `index.html` + `app.js` reads `data/papers.json` and `data/relations.json` and renders a Cytoscape graph with filters and a detail panel.

### Building graph data

Whenever you change records or taxonomy, rebuild the derived data:

```bash
python -m scripts.build_data
```

This validates records against the taxonomy and writes updated `data/papers.json` and `data/relations.json`.

### Markdown-only workflow (recommended for the team)

Researchers only need to work with markdown files in `notes/`.

1. **Create or update a note**
   - Copy `notes/_template.md` to a new file, for example:

   ```bash
   cp notes/_template.md notes/anotherpaper2022.md
   ```

   - Fill in the frontmatter and sections in the `.md` file:
     - Frontmatter between `---` lines: `id`, `title`, `authors`, `year`, `themes`, `methods`, `tensions`, `related`, `status`, `pdf`, `doi`, `source`.
     - Sections:
       - `# Summary` — 2–4 sentence summary.
       - `# Key Concepts` — bullet list of key concepts.
       - `# Notes` — free-form annotations.
       - `# Quotes` — one or more blockquoted lines starting with `>`.

2. **Ingest the note and rebuild graph data**

   ```bash
   python -m scripts.ingest_note notes/yarosh2022.md
   ```

   - The script:
     - Parses the frontmatter and sections from the markdown note.
     - Builds a record compatible with `records/*.json`.
     - Validates the record and taxonomy values.
     - Writes a normalized file to `records/<id>.json`.
     - Rebuilds `data/papers.json` and `data/relations.json`.

3. **View the updated graph**
   - Serve the repo with any static file server (for example):

   ```bash
   python -m http.server
   ```

   - Open `http://localhost:8000` in a browser to see the updated visualization.

### Advanced: ingesting raw JSON records

If you have a JSON file for a single paper in the same structure as the files in `records/` (for example, produced directly by an LLM), you can ingest it instead of a markdown note:

```bash
python -m scripts.ingest_record submissions/new-paper.json
```

To overwrite an existing record with the same `id`:

```bash
python -m scripts.ingest_record submissions/new-paper.json --overwrite
```

