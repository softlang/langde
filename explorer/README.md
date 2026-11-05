# langde ontology explorer

A read-only React + Vite + Cytoscape.js browser for the RDF graph in `../ontology/`.

## Run locally

Make sure your checkout has this layout:

```text
langde/
├── ontology/
│   ├── tbox.ttl
│   ├── abox-2025-2026.ttl
│   └── ...
└── explorer/
```

Prerequisites: Node.js 22 or later and Python 3.10+.

```sh
cd langde/explorer
python3 -m pip install -r requirements.txt
npm install             # first time; creates package-lock.json
npm run dev
```

Open http://localhost:5173/.

`npm run dev` calls `npm run prepare:data` first. The preparation script reads
**only** `tbox.ttl` and `abox-2025-2026.ttl`, as configured in
`data-sources.json`, and writes a union of asserted triples as N-Triples plus a
source manifest to `public/data/`.

`shapes.ttl`, generators and validation tools are *not* loaded into the browser.
The source ontology files are not modified. No endpoint, server-side database, or
SPARQL service is required. The browser works with static, generated data.

## Use

1. Search/select a named OWL/RDFS class on the left.
2. Filter/select an instance. Instance lists contain direct `rdf:type` assertions
   plus asserted instances of **named subclasses** (`rdfs:subClassOf`, transitive).
3. The graph displays incoming and outgoing RDF triples whose ends are resources.
   Arrowheads point from RDF subject to object, and edges are labeled by predicate.
4. Click any graph node to make it the new focus; **Back** returns to the previous focus.
5. Literals are in the details sidebar rather than rendered as graph nodes.

All object-property / resource-to-resource assertions are shown, including `rdf:type`
unless switched off in the UI. Anonymous RDF resources are navigable, but not shown
in the initial named-class selector. This version does **not** implement OWL
reasoning, SHACL validation, or recursive graph expansion. It uses assertions from
the provided files.

## Checks and build

```sh
npm run test:data        # Python preparation tests
npm run typecheck        # TypeScript type checking
npm run build            # prepare data, typecheck, generate explorer/dist/
npm run preview          # preview the build locally
```

`npm run build` assumes the ontology files exist next to `explorer/`.

## Deploy to GitHub Pages

1. Commit `explorer/` and `.github/workflows/deploy-explorer.yml` to `main`.
2. Commit the generated `explorer/package-lock.json` created by `npm install` if possible (recommended for reproducible builds).
3. Under **Settings → Pages** in the repository, select **GitHub Actions** as
   the source.
4. Push to `main`, or run **Deploy ontology explorer to GitHub Pages** manually
   under **Actions**.
5. Visit https://softlang.github.io/langde/ after the deploy completes.

The build uses Vite's `/langde/` base URL for GitHub Pages but `/` for local dev.

## Data and performance

The complete static RDF dataset is loaded into an N3.js in-memory store. Only
the selected resource's one-hop neighborhood is rendered in Cytoscape.js.
If the RDF dataset grows considerably, consider indexed, preprocessed JSON chunks
rather than a remote RDF service as the next incremental improvement.
