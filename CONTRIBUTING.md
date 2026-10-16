# 参与开发

项目由 Unity 主游戏、Blender 建模源文件和浏览器预览组成。功能与资产约定见 [项目规范](docs/project-standards.md)，验收步骤见 [测试说明](docs/testing.md)。

## 准备环境

- 浏览器预览：Python 3.9+、支持 WebGL 的现代浏览器，无需 npm 安装。
- 基础检查：Python 3.9+、Node.js 24。Node 仅用于 JavaScript 语法检查。
- Unity：以 `unity/ProjectSettings/ProjectVersion.txt` 为准，通过 Unity Hub 安装对应 Editor 和 Windows Build Support；依赖以 `unity/Packages/manifest.json` 为准。
- Blender：编辑现有 `.blend` 前保留原文件；在变更说明中记录实际使用的 Blender 版本和导出设置。
- PowerShell 7：需要执行 Unity 资源同步或独立 C# 语法检查时安装。

```sh
git clone https://github.com/MatildaHan/shanshui-courtyard.git
cd shanshui-courtyard
python3 start.py
```

Windows 可将 `python3` 换成 `python`。所有下面的命令从项目根目录执行。

## 开发流程

1. 更新 `main`，从最新提交创建 `feat/<主题>`、`fix/<主题>`、`docs/<主题>` 或 `chore/<主题>` 分支。
2. 保持一次改动围绕一个目的；代码、相关说明和验证证据一起更新。
3. 运行基础检查，并按 [测试说明](docs/testing.md) 完成对应运行端验收。
4. 检查差异后提交；合并请求说明问题、行为变化、验证结果和未验证部分。
5. 合并到 `main` 前由维护者确认检查结果。GitHub Actions 提供检查，但仓库分支保护需要维护者在 GitHub 设置中另行启用。

```sh
python3 tools/check-project.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
git status --short
git diff --stat
```

提交信息使用 `类型(范围): 说明`，说明可用中文，例如：

```text
feat(unity): 增加攀爬体力提示
fix(assets): 修正庭院门口碰撞偏移
docs(project): 补充资源导出规范
chore(ci): 增加模型同步检查
```

类型采用 `feat`、`fix`、`docs`、`refactor`、`test`、`chore`；范围可用 `unity`、`web`、`blender`、`assets`、`tools`、`ci`、`project`。不混入无关生成文件，也不强推共享分支。用户明确要求直接推送 `main` 时仍需通过对应检查，并使用普通快进推送。

## 资产与交付

共享模型在 `assets/` 更新后运行：

```sh
pwsh -NoProfile -File tools/sync-unity-assets.ps1 -RequireArchitecture
python3 tools/check-project.py
```

在 Unity Editor 中完成导入后，资源与生成的 `.meta` 一起提交；移动资源优先使用 Editor。当前源码中尚无完整 `.meta` 集合，首次建立稳定 GUID 基线时单独提交 Editor 实际生成的文件，不手工伪造。

离线单文件和源码交付包按需生成：

```sh
python3 tools/build-single.py
python3 tools/package.py
```

`dist/` 不提交，正式交付可附在 GitHub Release。Windows EXE 必须由 Unity 构建并实际启动验收。大资源遵守 [资源规则](docs/project-standards.md#资源与依赖)。

## 问题反馈与评审

反馈至少包含运行端、系统/浏览器或 Editor 版本、复现步骤、预期与实际结果，必要时附截图和相关日志片段。当前 fork 未启用 Issues，可通过合并请求说明问题，或由维护者启用 Issues 后使用问题模板。

只提交必要的日志片段；先移除个人目录、账号信息和密钥。第三方依赖保留许可证；项目自身目前未声明开源许可证，不能替权利人新增授权。
