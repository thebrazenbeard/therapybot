"""Run the browser-local adapter and synthetic DOM contracts in regular CI.

This supplements Python's unittest discovery; Node is optional for Python-only
local environments, but expected on the CI operating-system images.
"""

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConversationAdapterNodeContract(unittest.TestCase):
    def test_adapter_and_synthetic_dom_contracts(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not available")
        scripts = [
            ROOT / "tests" / "test_conversation_adapter.cjs",
            ROOT / "tests" / "test_adapter_dom_smoke.cjs",
        ]
        for script in scripts:
            self.assertTrue(script.is_file(), f"missing adapter contract: {script.name}")
        completed = subprocess.run(
            [node, "--test", *map(str, scripts)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"Adapter Node contracts failed:\n{completed.stdout}\n{completed.stderr}",
        )
