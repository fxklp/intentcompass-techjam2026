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
        """确保跨平台契约所需的配置文件已就位"""
        self.assertTrue(self.gitattributes.exists(), "Missing .gitattributes")
        self.assertTrue(self.editorconfig.exists(), "Missing .editorconfig")

    def test_git_check_attr_enforcement(self):
        """使用真实的 git check-attr 验证文件属性是否生效"""

        def check_attr(filepath, attr):
            result = subprocess.run(
                ["git", "check-attr", attr, "--", filepath],
                cwd=str(self.root), capture_output=True, text=True, check=True
            )
            return result.stdout.strip()

        # 检查 Python 文件是否被识别为 lf
        out_py = check_attr("fake_script.py", "eol")
        self.assertIn("lf", out_py.lower(), "Python files must enforce LF")

        # 检查图片文件是否被识别为 binary
        out_png = check_attr("fake_image.png", "binary")
        self.assertIn("set", out_png.lower(), "PNG files must be marked as binary")

    def test_binary_file_invariance_in_temp_repo(self):
        """在临时仓库中模拟 add/checkout，确保二进制字节绝对不变"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 将项目的 .gitattributes 复制到临时仓库
            shutil.copy(self.gitattributes, tmp_path / ".gitattributes")

            # 初始化临时 Git 仓库
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

            # --- 给 CI 的临时仓库一个身份 ---
            subprocess.run(["git", "config", "user.name", "CI Bot"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=tmpdir, check=True,
                           capture_output=True)

            # 伪造一个包含极易被 Windows Git 破坏的字节（\r\n 和 \n）的假二进制图片
            dummy_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            png_file = tmp_path / "test_image.png"
            png_file.write_bytes(dummy_bytes)

            # 提交到 Git
            subprocess.run(["git", "add", ".gitattributes", "test_image.png"], cwd=tmpdir, check=True,
                           capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir, check=True, capture_output=True)

            # 删除本地文件并从 Git 中强制检出
            png_file.unlink()
            subprocess.run(["git", "checkout", "test_image.png"], cwd=tmpdir, check=True, capture_output=True)

            # 读取检出后的字节，必须与原字节 100% 一致
            restored_bytes = png_file.read_bytes()
            self.assertEqual(dummy_bytes, restored_bytes, "Binary file bytes were corrupted by Git checkout!")
