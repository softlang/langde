"""Offline smoke test for langde's SHACL-SPARQL select queries.

This is NOT a substitute for pySHACL. It runs all SHACL-SPARQL queries
with RDFLib and checks the corrected exactly-one-German rule with bad data.
"""

from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import SH
from rdflib.plugins.sparql.parser import parseQuery

ROOT = Path(__file__).resolve().parent
LD = Namespace("http://www.uni-koblenz.de/ontologies/langde#")
tbox = Graph().parse(ROOT / "tbox.ttl")
abox = Graph().parse(ROOT / "abox-2025-2026.ttl")
shapes = Graph().parse(ROOT / "shapes.ttl")
data = tbox + abox
count = 0

for shape in shapes.subjects(RDF.type, SH.NodeShape):
    targets = set()
    for cls in shapes.objects(shape, SH.targetClass):
        targets.update(data.subjects(RDF.type, cls))
        for subclass in tbox.subjects(RDFS.subClassOf, cls):
            targets.update(data.subjects(RDF.type, subclass))
    focus_values = " ".join(f"<{uri}>" for uri in sorted(targets))
    for constraint in shapes.objects(shape, SH.sparql):
        sparql = str(shapes.value(constraint, SH.select))
        parseQuery(sparql)
        if "SELECT $this" not in sparql or "{ SELECT" in sparql:
            raise AssertionError("Unexpected SHACL-SPARQL SELECT layout")
        # The values clause tests all focus nodes at once without pySHACL.
        query = sparql.replace("$this", "?this").replace(
            "WHERE {", f"WHERE {{ VALUES ?this {{ {focus_values} }} ", 1
        )
        violations = list(data.query(query))
        if violations:
            msg = shapes.value(constraint, SH.message)
            raise AssertionError(f"{msg}: {violations[:3]}")
        count += 1

# Regression tests: the repaired constraint must detect both 0 and 2 German
# proficiency records for a student enrolled in a course.
course = next(data.subjects(RDF.type, LD.StandardCourse))
student = next(data.objects(course, LD.hasStudent))
prof = next(
    prof
    for prof in data.objects(student, LD.hasLanguageProficiency)
    if (prof, LD.proficiencyLanguage, LD.German) in data
)
course_shape = LD.CourseShape
rule = next(
    r
    for r in shapes.objects(course_shape, SH.sparql)
    if "exactly one German" in str(shapes.value(r, SH.message))
)
query = str(shapes.value(rule, SH.select)).replace("$this", "?this")

def detects_violation():
    return any(row.student == student for row in data.query(query, initBindings={"this": course}))

assert not detects_violation()
data.remove((student, LD.hasLanguageProficiency, prof))
assert detects_violation(), "Missing German proficiency was not detected"
data.add((student, LD.hasLanguageProficiency, prof))
extra_prof = LD.SmokeTestExtraGermanProficiency
data.add((student, LD.hasLanguageProficiency, extra_prof))
data.add((extra_prof, LD.proficiencyLanguage, LD.German))
assert detects_violation(), "Duplicate German proficiency was not detected"

print(f"PASS: {count} SHACL-SPARQL queries and two negative regression tests")
