from __future__ import annotations

import unittest

import tempfile

from pathlib import Path

from unittest.mock import patch

from scripts.team_gate import evaluation_threshold_violations, trailing_whitespace_lines, check_text_whitespace


PASSING_RESULT = {
    "sample_count": 200,
    "hit_rate_at_10": 0.75,
    "recommended_technical_score": 0.60,
    "scenario_metrics": {
        name: {"hit_rate_at_10": 0.60}
        for name in ("boundary", "browsing", "buying", "intent_override")
    },
}


class TeamGateThresholdTest(unittest.TestCase):
    def test_exact_milestone_thresholds_pass(self) -> None:
        self.assertEqual(evaluation_threshold_violations(PASSING_RESULT), [])

    def test_regression_and_missing_scenario_are_rejected(self) -> None:
        result = {
            **PASSING_RESULT,
            "hit_rate_at_10": 0.74,
            "recommended_technical_score": 0.59,
            "scenario_metrics": {
                "boundary": {"hit_rate_at_10": 0.59},
                "browsing": {"hit_rate_at_10": 0.90},
                "buying": {"hit_rate_at_10": 0.90},
            },
        }
        violations = "\n".join(evaluation_threshold_violations(result))
        self.assertIn("HitRate@10 must be >= 0.75", violations)
        self.assertIn("TechnicalScore must be >= 0.60", violations)
        self.assertIn("boundary HitRate@10 must be >= 0.60", violations)
        self.assertIn("missing scenario metrics: intent_override", violations)

    def test_trailing_whitespace_detection_covers_markdown_breaks_and_tabs(self) -> None:
        content = "clean\nmarkdown break  \ntrailing tab\t\nclean again\n"
        self.assertEqual(trailing_whitespace_lines(content), [2, 3])


class TestWhitespaceGateFileIO(unittest.TestCase):
    def setUp(self):
        # 创建临时目录存放测试文件，保证"实际读取"且不污染代码库
        self.test_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_1_detect_trailing_whitespace_in_utf8_file(self):
        """1. 实际读取临时 UTF-8 文件并发现行尾空格、Tab"""
        test_file = self.root_path / "bad_file.txt"
        test_file.write_text("line1 \nline2\t\nline3", encoding="utf-8")

        with patch('scripts.team_gate.ROOT', self.root_path):
            violations = check_text_whitespace({"bad_file.txt"})
            self.assertEqual(len(violations), 2)
            self.assertTrue(any("bad_file.txt:1" in v for v in violations))
            self.assertTrue(any("bad_file.txt:2" in v for v in violations))

    def test_2_normal_file_returns_empty(self):
        """2. 正常文件返回空结果"""
        test_file = self.root_path / "clean_file.txt"
        test_file.write_text("line1\nline2\nline3", encoding="utf-8")

        with patch('scripts.team_gate.ROOT', self.root_path):
            violations = check_text_whitespace({"clean_file.txt"})
            self.assertEqual(len(violations), 0)

    def test_3_invalid_utf8_safely_ignored(self):
        """3. 无效 UTF-8 文件不会导致门禁崩溃"""
        test_file = self.root_path / "invalid.txt"
        # 故意写入非 UTF-8 编码的字节，触发 UnicodeDecodeError
        test_file.write_bytes("测试乱码".encode("gbk"))

        with patch('scripts.team_gate.ROOT', self.root_path):
            violations = check_text_whitespace({"invalid.txt"})
            self.assertEqual(len(violations), 0)

    def test_4_nonexistent_or_nontext_ignored(self):
        """4. 不存在的文件或非文本文件会被安全忽略"""
        test_file_img = self.root_path / "image.png"
        test_file_img.write_bytes(b"fake image data")

        with patch('scripts.team_gate.ROOT', self.root_path):
            # 传入不存在的 missing.txt 和非文本的 image.png
            violations = check_text_whitespace({"missing.txt", "image.png"})
            self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
