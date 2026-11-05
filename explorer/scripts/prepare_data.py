#!/usr/bin/env python3
"""Assemble langde RDF sources into static N-Triples for the browser.

No generated RDF file is committed: the source of truth remains ../ontology/.
This is deliberately a lossless union of asserted triples, not OWL reasoning.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from rdflib import Dataset, Graph
except ImportError as exc:
    raise SystemExit("Missing rdflib. Run: python3 -m pip install -r requirements.txt") from exc

FORMATS = {
    ".ttl": "turtle", ".n3": "n3", ".nt": "nt", ".trig": "trig",
    ".nq": "nquads", ".rdf": "xml", ".owl": "xml", ".xml": "xml",
    ".jsonld": "json-ld",
}
IGNORE_PARTS = {
    "shacl", "shapes", "validation", "validations", "tests", "test",
    "fixtures", "examples", "reports", "report", "target", "results",
    "build", "dist", ".git",
}


def detect_format(path: Path) -> str:
    fmt = FORMATS[path.suffix.lower()]
    if path.suffix.lower() in {".owl", ".rdf", ".xml"}:
        beginning = path.read_bytes()[:1024].lstrip()
        if beginning.startswith((b"@prefix", b"@base", b"PREFIX", b"BASE")):
            return "turtle"
    return fmt


def discover_sources(root: Path, manual: list[str] | None) -> list[Path]:
    if manual is not None:
        sources = [root / p for p in manual]
        for path in sources:
            if not path.is_file() or not path.is_relative_to(root):
                raise ValueError(f"Configured source is missing or outside ontology/: {path}")
        return sorted(set(sources))

    paths = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in FORMATS:
            continue
        relative_parts = [part.lower() for part in p.relative_to(root).parts[:-1]]
        if any(part in IGNORE_PARTS or part.startswith(".") for part in relative_parts):
            continue
        if any(word in p.stem.lower() for word in ("shacl", "shape", "report", "validation")):
            continue
        # Only XML explicitly identified as RDF in its filename is considered:
        # a generic XML file is not necessarily an ontology.
        if p.suffix.lower() == ".xml" and not any(x in p.stem.lower() for x in ("ontology", "abox", "tbox", "rdf")):
            continue
        paths.append(p)
    return sorted(paths)


def build(ontology_root: Path, output: Path, source_config: Path | None) -> dict:
    root = ontology_root.resolve()
    if not root.is_dir():
        raise ValueError(f"Ontology directory not found: {root}. Place explorer/ beside ontology/.")

    include = None
    if source_config and source_config.is_file():
        config = json.loads(source_config.read_text(encoding="utf-8"))
        include = config["include"]
        if not isinstance(include, list) or not all(isinstance(s, str) for s in include):
            raise ValueError("data-sources.json must contain an 'include' array of relative paths")

    sources = discover_sources(root, include)
    if not sources:
        raise ValueError(f"No RDF files detected under {root}; configure data-sources.json explicitly.")

    combined = Graph()
    log = []
    for file in sources:
        rdf_format = detect_format(file)
        try:
            if rdf_format in {"trig", "nquads"}:
                dataset = Dataset()
                dataset.parse(file, format=rdf_format, publicID=file.as_uri())
                quads = [(s, p, o) for s, p, o, _ in dataset.quads((None, None, None, None))]
            else:
                parsed = Graph()
                parsed.parse(file, format=rdf_format, publicID=file.as_uri())
                quads = list(parsed)
        except Exception as exc:
            raise ValueError(f"Cannot parse {file.relative_to(root)} as {rdf_format}: {exc}") from exc
        for triple in quads:
            combined.add(triple)
        log.append({"file": file.relative_to(root).as_posix(), "format": rdf_format, "triples": len(quads)})

    output.mkdir(parents=True, exist_ok=True)
    rdf_path = output / "ontology.nt"
    rdf_path.write_text(combined.serialize(format="nt"), encoding="utf-8")
    manifest = {"triples": len(combined), "sources": log, "format": "N-Triples"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    explorer = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ontology-root", type=Path, default=explorer.parent / "ontology")
    parser.add_argument("--output", type=Path, default=explorer / "public" / "data")
    parser.add_argument("--config", type=Path, default=explorer / "data-sources.json")
    args = parser.parse_args()
    try:
        manifest = build(args.ontology_root, args.output, args.config)
    except (ValueError, OSError, KeyError) as exc:
        print(f"Data preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Prepared {manifest['triples']} triples from {len(manifest['sources'])} RDF files:")
    for source in manifest["sources"]:
        print(f"  - {source['file']} ({source['format']}, {source['triples']} triples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
