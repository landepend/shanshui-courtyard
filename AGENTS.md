# 项目协作约定

本文件适用于整个仓库。完整开发规则见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [项目规范](docs/project-standards.md)。

- Unity 是主游戏工程；浏览器版是独立预览。报告验证结果时注明运行端。
- 修改前阅读相关模块和已有验证记录。保留用户未提交的工作，避免无关重构和全仓库格式化。
- 浏览器保持原生 ES Modules、本地 Three.js 和离线资源加载；不因普通功能改动引入 npm 或远程 CDN。
- 共享模型以 `assets/` 为准；修改后同步 Unity 副本，保留动画名称、建筑 `part` 和坐标转换契约。
- Unity 资源与已有 `.meta` 一起提交。新资源由 Editor 生成 `.meta`，不得随意重建已有 GUID。
- 工具从脚本位置定位项目根目录；不得写入开发者机器的绝对路径、凭证或本地 MCP 配置。
- 修改代码后运行 `python3 tools/check-project.py` 和 `python3 -m unittest discover -s tests -p 'test_*.py' -v`，按变更范围补充浏览器或 Unity 实测。
- 静态检查、MCP 握手、Unity 编译、Play Mode 和 Windows 构建是不同结果；未实际执行必须标记“未验证”。
- 不编辑 `vendor/` 和 `archive/`，除非任务确实要求升级依赖或维护历史版本。依赖升级单独说明版本和许可证。
- 提交前检查 `git diff --check`、资源体积和暂存清单。缓存、密钥、日志、生成的交付物不进入源码提交。
- 只有用户明确要求时才推送、发布或向外部发送消息；推送采用普通快进，禁止擅自强推或重写远端历史。
