# langde — synthetic course ontology (school year 2025/2026)

An experiment with a particular German language school design as a synthesized variation on https://wp.uni-koblenz.de/funkprojekt/

Files: `tbox.ttl` (OWL vocabulary), `abox-2025-2026.ttl` (fictional individuals), `shapes.ttl` (SHACL), `summary.json` (metrics), `Makefile` (validation), `requirements.txt` (Python dependencies), `generate.py` (reproducible generation), `smoke_shacl_sparql.py` (SPARQL regression checks).

Ontology IRI: `http://www.uni-koblenz.de/ontologies/langde`
Prefix: `ld:` = `http://www.uni-koblenz.de/ontologies/langde#`.

## SHACL validation
Run `make install` once to install dependencies, then `make validate` to validate the A-Box with the T-Box and SHACL shapes. `make smoke` checks the SHACL-SPARQL queries using RDFLib (including negative regression cases) without running the full SHACL engine. `make check` runs both smoke checks and pySHACL validation. `make regenerate` recreates the Turtle files from `generate.py` (and the summary/README).

## Dataset
- 10 courses (8 standard, 2 preparatory); 232 sessions, 51 students, 12 teachers, 6 entirely fictional schools.
- 31 session-absence assertions and 15 substitute-session assertions.
- Student ages at school-year start are within 11–21, mostly age-appropriate for grades 9–13.
- German CEFR ranks: A1=1, A2=2, B1=3, B2=4, C1=5, C2=6. Standard courses require rank >=3 (B1); preparatory courses require rank >=2 (A2) as an explicit **synthetic assumption**: the user's lower cutoff for preparatory courses was not settled, so generated A1 examples are excluded by the chosen local threshold.
- Two or more general subjects on Course10, with session topics from the permitted subject areas.
- Every synthetic student attends exactly one course. Student school/grade affiliation is modeled directly.

## Calendaring
- Session dates are between 2025-08-18 and 2026-06-26, Monday–Friday, avoiding official RLP autumn (2025-10-13–24), Christmas (2025-12-22–2026-01-07), Easter (2026-03-30–04-10), and 2026 summer (from 2026-06-29) holidays, and state public holidays.
- Also conservatively avoid representative Carnival/bridge-day dates (2026-02-12–18, 2026-05-15, 2026-06-05). These are NOT uniform state-wide school holidays; each school has its own movable days. The dataset does not assert that each fictional school uses an official school-specific calendar.
- Sources: https://bm.rlp.de/service/ferientermine/seite ; https://mdi.rlp.de/themen/buerger-und-staat/verfassung-und-verwaltung/sonn-und-feiertagsrecht

## Semantics and validation
- OWL intentionally uses open-world semantics. For closed-world completeness, numerical ranges, cross-property consistency, holiday exclusion, and admission checks, use SHACL.
- SHACL SPARQL checks require a SHACL engine implementing SPARQL constraints.
- Native-language German exclusion is expressed in both OWL and SHACL.
- Explicit `enrolledIn` and `hasStudent` / `sessionOf` and `hasSession` are mutually inverse.
- `requiredGermanRank` is a course-level *test data rule*, and the preparatory A2 threshold is provisional.
- Session scheduling is synthetic; rooms, timetable clashes, student consent and personally identifiable real records are deliberately absent.
