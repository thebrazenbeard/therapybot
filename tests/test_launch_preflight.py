"""Offline-by-default launcher behavior, without installing packages or models."""

import os
import shutil
import subprocess
import tempfile
import unittest
import importlib.util
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LinuxLauncherTests(unittest.TestCase):
    def _sandbox(self, base):
        root = Path(base)
        (root / "launch").mkdir(parents=True)
        (root / ".venv" / "bin").mkdir(parents=True)
        shutil.copy2(ROOT / "launch" / "start-linux.sh", root / "launch" / "start-linux.sh")
        fake_python = root / ".venv" / "bin" / "python"
        fake_python.write_text(
            '#!/bin/sh\n'
            'printf "%s\\n" "$*" >> "$THERAPYBOT_TEST_LOG"\n'
            'exit 0\n', encoding="utf-8"
        )
        fake_python.chmod(0o700)
        return root

    def _run(self, root, *args, cwd=None):
        log = root / "python_calls.log"
        env = {**os.environ, "THERAPYBOT_TEST_LOG": str(log)}
        completed = subprocess.run(
            ["sh", str(root / "launch" / "start-linux.sh"), *args],
            cwd=cwd or root, env=env, text=True, capture_output=True, timeout=15,
        )
        return completed, log.read_text(encoding="utf-8") if log.exists() else ""

    def test_normal_launch_does_not_run_pip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            result, log = self._run(root, "--no-browser")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("-m pip install", log)
            self.assertIn("launch/preflight.py", log)
            self.assertIn("-m therapybot --no-browser", log)

    def test_check_does_not_start_http_or_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            result, log = self._run(root, "--check")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("launch/preflight.py", log)
            self.assertNotIn("-m therapybot", log)
            self.assertNotIn("-m pip install", log)

    def test_explicit_setup_is_only_network_capable_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            result, log = self._run(root, "--setup")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("-m pip install -r requirements.txt", log)
            self.assertNotIn("-m therapybot", log)

    def test_offline_setup_disables_package_index(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            wheels = root / "wheels"
            wheels.mkdir()
            result, log = self._run(root, "--setup-offline", str(wheels))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("-m pip --isolated install --no-index --find-links", log)
            self.assertNotIn("-m therapybot", log)

    def test_offline_setup_relative_path_is_relative_to_caller(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(Path(folder) / "app")
            caller = Path(folder) / "caller"
            wheels = caller / "local wheels"
            wheels.mkdir(parents=True)
            result, log = self._run(root, "--setup-offline", "local wheels", cwd=caller)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--find-links " + str(wheels), log)
            self.assertIn("--no-index", log)

    def test_offline_setup_rejects_no_or_empty_path_before_pip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            for arguments in (("--setup-offline",), ("--setup-offline", "")):
                with self.subTest(arguments=arguments):
                    result, log = self._run(root, *arguments)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(log, "")

    def test_offline_setup_rejects_missing_wheel_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            result, log = self._run(root, "--setup-offline", str(root / "missing"))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(log, "")

    def test_normal_start_does_not_create_missing_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._sandbox(folder)
            (root / ".venv" / "bin" / "python").unlink()
            result, log = self._run(root, "--no-browser")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(log, "")
            self.assertFalse((root / ".venv" / "bin" / "python").exists())
            self.assertIn("environment missing", result.stderr.lower())


class WindowsLauncherSourceTests(unittest.TestCase):
    def test_windows_launcher_explicit_setup_and_offline_preflight(self):
        source = (ROOT / "launch" / "start-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("-Setup", source)
        self.assertIn("-Check", source)
        self.assertIn("preflight.py", source)
        self.assertIn("pip install", source)
        self.assertIn("--no-index", source)
        self.assertIn("--isolated", source)
        self.assertIn("IsNullOrWhiteSpace", source)
        self.assertIn("$Mode -eq 'setup-offline'", source)
        self.assertIn("$InvocationDirectory", source)


class RuntimePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "launch" / "preflight.py"
        spec = importlib.util.spec_from_file_location("therapybot_launch_preflight_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.module = module

    def test_valid_release_range(self):
        for version in ("43.0.0", "50.0.1"):
            with self.subTest(version=version):
                with mock.patch.object(self.module.importlib.metadata, "version", return_value=version):
                    self.assertEqual(self.module.check_runtime(), 0)

    def test_old_future_and_prerelease_versions_are_rejected(self):
        for version in ("41.0.7", "51.0.0", "43.0.0rc1"):
            with self.subTest(version=version):
                with mock.patch.object(self.module.importlib.metadata, "version", return_value=version):
                    self.assertEqual(self.module.check_runtime(), 2)

    def test_missing_dependency_rejected(self):
        with mock.patch.object(
            self.module.importlib.metadata, "version",
            side_effect=self.module.importlib.metadata.PackageNotFoundError("cryptography"),
        ):
            self.assertEqual(self.module.check_runtime(), 2)

    def test_python_before_310_rejected_before_dependency_query(self):
        with mock.patch.object(self.module.sys, "version_info", (3, 9)):
            with mock.patch.object(self.module.importlib.metadata, "version") as lookup:
                self.assertEqual(self.module.check_runtime(), 2)
                lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
