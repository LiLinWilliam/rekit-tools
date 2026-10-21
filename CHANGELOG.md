# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

No unreleased changes.

## [1.0.2] - 2026-10-21

### Added

- A visual README header, complete badge row, table of contents, Mermaid recovery flow, FAQ, roadmap, and design principles in English and Chinese.
- Verified `--version` output examples in all 12 tool READMEs.
- A GitHub Pages documentation workflow, static landing page, tool cards, and published documentation link.
- Contributor Covenant, pre-commit hooks, expanded Ruff rules, measured coverage diagnostics, and stable tool exit-code documentation.
- A dependency-free PowerShell smoke job that parses all checked-in scripts and exercises the watchdog lifecycle with mocks.
- Searchable static Pages for all 12 tools, including result feedback, responsive navigation, Back to top controls, and Edit on GitHub links.
- Exit-code and security-note sections in every tool README, linked to the repository contracts.

### Changed

- The single version source is now `1.0.2`; all Python entry points and their tests read it consistently.
- CI reports the measured 49.35% `tools/` coverage from 49 tests and enforces a 49% floor.
- CI dependencies use the same pytest-cov major version locally and on the matrix runners.
- CONTRIBUTING now includes a copy/paste validation block and the repository's issue-label meanings.

## [1.0.1] - 2026-10-21

### Fixed

- 修正 README 中 CI 徽章的换行，使徽章链接在 GitHub 上保持可读。

## [1.0.0] - 2026-10-21

### Added

- 面向 Windows 的 12 个独立工具：健康检查、环境快照、离线恢复、迁移验证、熵图渲染、原生 launcher、工具链安装和 Codex retry-watchdog。
- 持续集成、pytest 单元测试、覆盖率输出、Issue/PR 模板、贡献指南和安全报告流程。
- `render-entropy`、`restore`、`verify`、`verify-portability` 等最小用法示例。

### Security

- 发布公开仓库安全说明，明确不提交凭据、私有样本、会话数据库、日志和本地工具链。

[Unreleased]: https://github.com/LiLinWilliam/rekit-tools/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/LiLinWilliam/rekit-tools/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/LiLinWilliam/rekit-tools/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/LiLinWilliam/rekit-tools/releases/tag/v1.0.0
