import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_wordbank.py"
FIXTURE = ROOT / "tests" / "fixtures" / "ecdict_sample.csv"
CURATED = ROOT / "curated" / "field_english_professional.csv"


class BuildWordbankTests(unittest.TestCase):
    def test_filters_deduplicates_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            output = temp / "field_english_words.csv"
            manifest = temp / "manifest.json"
            manifest.write_text(json.dumps({
                "version": "1.0.0",
                "version_code": 1,
                "content": {
                    "sha256": "old",
                    "url": "https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/field_english_words.csv"
                },
                "update_policy": {"offline_fallback": True}
            }), encoding="utf-8")

            subprocess.run([
                sys.executable, str(SCRIPT),
                "--source", str(FIXTURE),
                "--curated", str(CURATED),
                "--output", str(output),
                "--manifest", str(manifest)
            ], check=True)

            with output.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            words = {row["英文"].casefold() for row in rows}
            self.assertIn("network", words)
            self.assertIn("router", words)
            self.assertIn("hello", words)
            self.assertIn("cloud computing", words)
            self.assertNotIn("rareword", words)
            self.assertEqual(len(words), len(rows))
            self.assertIn("BGP peer", {row["英文"] for row in rows})
            self.assertEqual(len(rows), 129)

            built_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(built_manifest["content"]["count"], len(rows))
            self.assertEqual(built_manifest["version_code"], 2)
            self.assertEqual(len(built_manifest["content"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
