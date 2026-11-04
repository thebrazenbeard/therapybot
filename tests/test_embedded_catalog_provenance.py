"""Registry identity contract for embedded, user-facing background reading.

This checks links and bibliographic identity, not claims of clinical efficacy,
research content rights, model-training rights, or medical safety.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
EXCEPTIONAL_HELP_LINK = ("988", "https://988lifeline.org/get-help/")


PROBE = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const window = {};
const context = vm.createContext({window});
for (const file of process.argv.slice(1)) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, {filename: file, timeout: 1500});
}
const catalog = window.TherapyBotEmbeddedCatalog;
const engine = window.TherapyBotEmbedded;
const prompts = [
  'My boss is asking me to pay for work expenses.',
  'My relationships are strained and I feel lonely.',
  'I want to understand how psychotherapy helps with my moods.',
  'I feel overwhelmed and isolated.',
  'I need to set boundaries at work.'
];
const displayed = prompts.map(message => engine.respond({message}).sources).flat();
console.log(JSON.stringify({catalog, displayed}));
"""


@unittest.skipUnless(NODE, "Node.js is required to execute embedded sources")
class EmbeddedCatalogProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completed = subprocess.run(
            [NODE, "-e", PROBE, str(ROOT / "embedded/catalog.js"), str(ROOT / "embedded/engine.js")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        cls.probe = json.loads(completed.stdout)
        cls.registry = {record["id"]: record for record in json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))}

    def _validate_references(self, records):
        failures = []
        for record in records:
            source_id, url = record["id"], record["url"]
            if (source_id, url) == EXCEPTIONAL_HELP_LINK:
                continue  # Operational U.S. crisis-help link, not research citation.
            canonical = self.registry.get(source_id)
            if canonical is None:
                failures.append(f"{source_id}: absent from research/sources.json (URL {url})")
            elif canonical["url"] != url:
                failures.append(f"{source_id}: URL differs (catalog {url}, registry {canonical['url']})")
        self.assertEqual(failures, [], "Every displayed non-emergency citation must match canonical ID and URL")

    def test_catalog_links_use_canonical_identifiers_and_urls(self):
        records = self.probe["catalog"]
        self.assertGreaterEqual(len(records), 5)
        self.assertEqual(len({item["id"] for item in records}), len(records), "duplicate catalog IDs")
        self.assertEqual(
            [item for item in records if item["id"] == "988"],
            [item for item in records if (item["id"], item["url"]) == EXCEPTIONAL_HELP_LINK],
            "the sole 988 exception must remain the exact operational help URL",
        )
        self._validate_references(records)

    def test_rendered_engine_citations_use_canonical_identifiers_and_urls(self):
        records = self.probe["displayed"]
        self.assertGreater(len(records), 0, "no citations emitted by representative conversations")
        self._validate_references(records)


if __name__ == "__main__":
    unittest.main()
