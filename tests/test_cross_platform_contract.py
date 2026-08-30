import unittest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path


class TestCrossPlatformContract(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent
        self.gitattributes = self.root / ".gitattributes"
        self.editorconfig = self.root / ".editorconfig"

    def test_configuration_files_exist(self):
        """Ensure cross-platform contract config files exist"""
        self.assertTrue(self.gitattributes.exists(), "Missing .gitattributes")
        self.assertTrue(self.editorconfig.exists(), "Missing .editorconfig")

    def _get_git_attr(self, filepath, attr):
        """精确解析 git check-attr 的返回值"""
        result = subprocess.run(
            ["git", "check-attr", attr, "--", filepath],
            cwd=str(self.root), capture_output=True, text=True, check=True
        )
        # Git 输出格式例如: "fake_image.png: binary: set"
        output = result.stdout.strip()
        if output:
            return output.split(":")[-1].strip()
        return "unspecified"

    def test_git_check_attr_enforcement(self):
        """精确校验 Git 属性，包含正例与负例 (Positive & Negative Cases)"""
        # 1. 正例 (Positive Cases)
        py_eol = self._get_git_attr("fake_script.py", "eol")
        self.assertEqual(py_eol, "lf", "Python files must enforce LF")

        png_binary = self._get_git_attr("fake_image.png", "binary")
        self.assertEqual(png_binary, "set", "PNG files must be marked as binary")

        # 2. 负例 (Negative Cases) - Python脚本不能被误判为 binary
        py_binary = self._get_git_attr("fake_script.py", "binary")
        self.assertIn(py_binary, ["unset", "unspecified"], "Python scripts should not be binary")

    def test_binary_file_invariance_in_temp_repo(self):
        """Simulate add/checkout in temp repo to ensure binary bytes are untouched"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            shutil.copy(self.gitattributes, tmp_path / ".gitattributes")
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "CI Bot"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=tmpdir, check=True,
                           capture_output=True)

            dummy_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            png_file = tmp_path / "test_image.png"
            png_file.write_bytes(dummy_bytes)

            subprocess.run(["git", "add", ".gitattributes", "test_image.png"], cwd=tmpdir, check=True,
                           capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir, check=True, capture_output=True)

            png_file.unlink()
            subprocess.run(["git", "checkout", "test_image.png"], cwd=tmpdir, check=True, capture_output=True)

            restored_bytes = png_file.read_bytes()
            self.assertEqual(dummy_bytes, restored_bytes, "Binary file bytes were corrupted by Git checkout!")
