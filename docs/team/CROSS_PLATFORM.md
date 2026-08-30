# 跨平台协作规范

为保证 Windows, macOS, Linux 开发者体验一致，本项目实施以下跨平台契约：

1. **换行符规范**：所有文本文件（Python, Markdown, JSON, YAML等）必须使用 `LF (\n)` 换行。受 `.editorconfig` 和 `.gitattributes` 强制保护。
2. **二进制安全**：图片（PNG/JPG）和 PDF 等二进制文件严禁被 Git 转换换行符。
3. **自动化验证**：GitHub Actions 将同时在 `ubuntu-latest`, `macos-latest`, `windows-latest` 矩阵中运行测试与门禁。
