import unittest
import os
from pathlib import Path

class TestCrossPlatformContract(unittest.TestCase):
    def test_configuration_files_exist(self):
        """确保跨平台契约所需的配置文件已就位"""
        root = Path(__file__).parent.parent
        self.assertTrue((root / ".gitattributes").exists(), "Missing .gitattributes")
        self.assertTrue((root / ".editorconfig").exists(), "Missing .editorconfig")

    def test_line_endings_config(self):
        """检查 .gitattributes 中是否配置了 LF 和 binary"""
        attr_file = Path(__file__).parent.parent / ".gitattributes"
        content = attr_file.read_text(encoding="utf-8").lower()
        self.assertIn("eol=lf", content)
        self.assertIn("binary", content)
