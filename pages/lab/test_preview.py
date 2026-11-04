"""Source-only smoke contracts for the isolated rules-based browser lab."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from build_preview import LAB, REPO, LAB_FILES, RUNTIME_FILES, build


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PreviewTests(unittest.TestCase):
    def test_exact_allowlist_copy_and_no_secret_or_model_files(self):
        with tempfile.TemporaryDirectory() as temp:
            out = build(Path(temp) / "lab-build")
            expected = set(LAB_FILES) | {"runtime/" + name for name in RUNTIME_FILES}
            actual = {str(p.relative_to(out)).replace("\\", "/") for p in out.rglob("*") if p.is_file()}
            self.assertEqual(actual, expected)
            for name in LAB_FILES:
                self.assertEqual(sha256(out / name), sha256(LAB / name))
            for name in RUNTIME_FILES:
                self.assertEqual(sha256(out / "runtime" / name), sha256(REPO / "embedded" / name))
            self.assertFalse(any(p.suffix in (".gguf", ".sqlite", ".env") for p in out.rglob("*")))

    def test_live_composer_and_explicit_optional_neural(self):
        html = (LAB / "index.html").read_text(encoding="utf-8")
        js = (LAB / "lab.js").read_text(encoding="utf-8")
        self.assertIn('id="composer"', html)
        self.assertIn('id="message"', html)
        self.assertIn('id="conversation-log"', html)
        self.assertIn('class="helpbar"', html)
        self.assertNotIn('Unvalidated safety route:', js)
        self.assertIn("connect-src 'self' https://huggingface.co", html)
        self.assertIn('id="model-consent"', html)
        self.assertIn('id="pause"', html)
        self.assertIn('src="./neural.js"', html)
        self.assertIn('runtime/conversation_adapter.js', html)
        self.assertIn("session.turn(", js)
        self.assertIn("textContent = message", js)
        self.assertIn('let transcript = []', js)
        self.assertIn('acuteContext', js)
        self.assertIn('paused', js)
        self.assertIn('outputGate: reviewNeuralOutput', js)
        self.assertIn("kind: 'in-browser-neural'", js)
        neural = (LAB / 'neural.js').read_text(encoding='utf-8')
        self.assertIn('loadModel([file]', neural)
        self.assertNotIn('loadModelFromUrl', neural)
        self.assertNotIn('indexedDB', neural)
        self.assertNotIn('localStorage', neural)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("indexedDB", js)

    def test_non_empty_target_rejected_without_clobber(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "occupied"
            out.mkdir()
            marker = out / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(out)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()
