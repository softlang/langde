PYTHON ?= python3
PYSHACL = $(PYTHON) -m pyshacl
ABOX = abox-2025-2026.ttl
TBOX = tbox.ttl
SHAPES = shapes.ttl

.PHONY: install validate smoke check regenerate

install:
	$(PYTHON) -m pip install -r requirements.txt

# The ontology graph is supplied separately to validate instance data against
# subclass/range declarations as well as SPARQL-based SHACL constraints.
# pySHACL returns a nonzero exit code when validation fails.
validate:
	$(PYSHACL) -s $(SHAPES) -e $(TBOX) -i rdfs -f human $(ABOX)

# Fast RDFLib smoke test; validates SPARQL behavior, not full SHACL semantics.
smoke:
	$(PYTHON) smoke_shacl_sparql.py

check: smoke validate

regenerate:
	$(PYTHON) generate.py
