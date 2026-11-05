"""Data preparation smoke tests; fixtures are generated in a temporary directory."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_data import build


class PrepareDataTests(unittest.TestCase):
    def test_merges_tbox_abox_and_skips_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ontology"
            (root / "schema").mkdir(parents=True)
            (root / "data").mkdir()
            (root / "validation").mkdir()
            (root / "schema" / "tbox.ttl").write_text(
                "@prefix ex: <https://example.org/> .\n"
                "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                "ex:Person a owl:Class .\n",
                encoding="utf-8",
            )
            (root / "data" / "abox.ttl").write_text(
                "@prefix ex: <https://example.org/> .\n"
                "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
                "ex:alice rdf:type ex:Person ; ex:knows ex:bob .\n"
                "ex:bob ex:knows ex:alice .\n",
                encoding="utf-8",
            )
            (root / "validation" / "shape.ttl").write_text(
                "@prefix ex: <https://example.org/> . ex:garbage ex:p ex:o .",
                encoding="utf-8",
            )
            manifest = build(root, Path(tmp) / "public", None)
            self.assertEqual(manifest["triples"], 4)
            self.assertEqual(len(manifest["sources"]), 2)
            output = (Path(tmp) / "public" / "ontology.nt").read_text()
            self.assertNotIn("garbage", output)
            self.assertIn("alice", output)

    def test_manual_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ontology"
            root.mkdir()
            (root / "one.ttl").write_text("<urn:a> <urn:p> <urn:b> .\n")
            (root / "two.ttl").write_text("<urn:b> <urn:p> <urn:c> .\n")
            conf = Path(tmp) / "sources.json"
            conf.write_text('{"include": ["two.ttl"]}')
            manifest = build(root, Path(tmp) / "public", conf)
            self.assertEqual(manifest["triples"], 1)
            self.assertEqual(manifest["sources"][0]["file"], "two.ttl")


if __name__ == "__main__":
    unittest.main()
