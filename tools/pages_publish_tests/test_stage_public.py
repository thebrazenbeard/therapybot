"""Offline release guard: the experimental browser lab must never be staged."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage_public import PUBLIC_FILES, stage_public


class PagesPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pages = self.root / 'pages'
        self.pages.mkdir()
        for name in PUBLIC_FILES:
            (self.pages / name).write_text('safe-' + name, encoding='utf-8')
        self.lab = self.pages / 'lab'
        self.lab.mkdir()
        (self.lab / 'index.html').write_text('EXPERIMENTAL CHAT', encoding='utf-8')
        (self.pages / 'new-page.html').write_text('FUTURE UNREVIEWED', encoding='utf-8')
    def test_exact_allowlist_and_preserved_content(self):
        output = self.root / 'artifact'
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.pages.iterdir() if p.is_file()}
        stage_public(self.pages, output)
        self.assertEqual({p.name for p in output.rglob('*') if p.is_file()}, set(PUBLIC_FILES))
        self.assertFalse((output / 'lab').exists())
        self.assertFalse((output / 'new-page.html').exists())
        for name in PUBLIC_FILES:
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), before[name])

    def test_missing_preview_fails_before_artifact_creation(self):
        (self.pages / PUBLIC_FILES[0]).unlink()
        output = self.root / 'artifact'
        with self.assertRaises(ValueError):
            stage_public(self.pages, output)
        self.assertFalse(output.exists())

    def test_existing_artifact_refused(self):
        output = self.root / 'artifact'
        output.mkdir()
        (output / 'private.txt').write_text('private', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            stage_public(self.pages, output)
        self.assertTrue((output / 'private.txt').exists())
    def test_allowlisted_symlink_refused(self):
        source = self.pages / PUBLIC_FILES[0]
        source.unlink()
        try:
            source.symlink_to(self.lab / 'index.html')
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable on this host')
        output = self.root / 'artifact'
        with self.assertRaises(ValueError):
            stage_public(self.pages, output)
        self.assertFalse(output.exists())

    def test_output_inside_source_is_refused(self):
        with self.assertRaises(ValueError):
            stage_public(self.pages, self.pages / 'nested-artifact')

    def test_checked_in_public_preview_links_and_noninteractive_shell(self):
        pages = Path(__file__).resolve().parents[2] / 'pages'
        index = (pages / 'index.html').read_text(encoding='utf-8')
        preview = (pages / 'interface-preview.html').read_text(encoding='utf-8')
        self.assertIn('href="interface-preview.html"', index)
        self.assertIn('href="interface-preview.css"', preview)
        for html in (index, preview):
            for forbidden in ('<script', '<form', '<textarea', '<input', 'href="lab/'):
                self.assertNotIn(forbidden, html.lower())

    def test_real_repository_cli_stages_exact_public_site(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / 'artifact'
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent / 'stage_public.py'),
                 '--source', 'pages', '--destination', str(artifact)],
                cwd=repo, capture_output=True, text=True, check=True)
            self.assertIn('staged-public-pages=', completed.stdout)
            self.assertEqual({p.name for p in artifact.rglob('*') if p.is_file()},
                             set(PUBLIC_FILES))
            self.assertFalse((artifact / 'lab').exists())

    def test_workflow_only_uploads_allowlisted_staging_directory(self):
        workflow = (Path(__file__).resolve().parents[2] / '.github' / 'workflows'
                    / 'static.yml').read_text(encoding='utf-8')
        self.assertIn('stage_public.py --source pages --destination', workflow)
        self.assertIn("path: '${{ runner.temp }}/therapybot-public-pages'", workflow)
        self.assertNotIn("path: 'pages'", workflow)


if __name__ == '__main__':
    unittest.main()
