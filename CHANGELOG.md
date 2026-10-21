# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- README 展示区、由真实 `render-entropy` 输出生成的压缩示例图和可复现终端命令。
- 12 个工具 README 的完整用法、输入输出、退出码和安全边界说明。
- `environment-snapshot` 与 `retry-watchdog` 的纯函数和临时 SQLite 测试。
- Windows Python 3.10、3.11、3.12 的 CI 矩阵。
- tag 触发的 GitHub Release notes 工作流和分类配置。
- 安全边界与授权使用文档。

### Changed

- 测试覆盖率从 23% 提升到 37%，当前测试套件为 20 passed。

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

[Unreleased]: https://github.com/LiLinWilliam/rekit-tools/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/LiLinWilliam/rekit-tools/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/LiLinWilliam/rekit-tools/releases/tag/v1.0.0
