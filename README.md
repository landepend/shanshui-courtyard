# 山水楼阁 · 阿棠行记

包含 Unity 游戏项目、Blender 建模源文件和浏览器预览版。

## 克隆项目

公开仓库，任何人都可以克隆或通过 GitHub 的 **Code → Download ZIP** 下载。

```sh
git clone https://github.com/MatildaHan/shanshui-courtyard.git
cd shanshui-courtyard
```

已有本地副本可在项目目录运行 `git pull` 获取更新。

## 浏览器预览

安装 Python 3.9 或更新版本，然后运行：

```sh
python start.py
```

启动后会自动打开浏览器。第三方 JavaScript 库和模型已包含在仓库内，无需 npm 安装。

## Cloudflare Pages 部署浏览器预览

Pages 的单个文件上限是 25 MiB，建筑 GLB 为 27.77 MiB，不能把仓库根目录直接作为发布目录。
在 Pages 的构建设置中选择框架 `None`，填写：

- 构建命令：`python3 tools/build-pages.py`
- 构建输出目录：`dist/pages`
- 根目录：留空（仓库根目录）

构建工具仅使用 Python 标准库，将建筑 GLB 无损重打包为 glTF 和多个不超过 16 MiB 的本地数据文件，
保留几何、材质、坐标和构件标识。只发布浏览器所需资源，并检查所有输出文件不超过 25 MiB。
共享 GLB、Unity 副本与离线单文件流程不变；`dist/pages/` 是生成目录，不提交。
限制与设置详见 [Pages 文件限制](https://developers.cloudflare.com/pages/platform/limits/) 和
[构建配置](https://developers.cloudflare.com/pages/configuration/build-configuration/)。

本地检查发布目录：

```sh
python3 tools/build-pages.py
python3 -m http.server 8000 --directory dist/pages
```

打开 `http://127.0.0.1:8000/` 验证建筑载入与交互。已有 Pages 项目需保存上述构建设置后重新部署。

## Unity 项目

使用 Unity Hub 打开 `unity` 文件夹。编辑器版本见 `unity/ProjectSettings/ProjectVersion.txt`，依赖见 `unity/Packages/manifest.json`；首次打开需要联网安装依赖，并在系统中安装 Git。

具体操作和项目状态见 [项目说明](README.txt) 和 [Unity 说明](unity/README.txt)。现有记录尚未确认 Unity 编译、Play Mode 或 Windows EXE 构建成功。

## 目录

- `unity/`：Unity 项目源码与模型资源。
- `blender/`：Blender 源文件与建模脚本。
- `assets/`：跨引擎模型和设定图。
- `src/`、`index.html`、`vendor/`：浏览器预览版及依赖。
- `docs/`、`tests/`：说明、截图、测试脚本与已有验证记录。
- `tools/`：资源同步、打包及辅助工具。
- `archive/`：历史版本。

构建输出 `dist/`、编辑器缓存、日志和 Blender 自动备份未纳入版本控制。预览版可直接从源码启动。

## 离线单文件与交付包

以下工具均使用 Python 标准库；在 Windows 可把 `python3` 换成 `python`。
路径由脚本所在位置确定，从其他工作目录调用也可运行，支持空格和中文目录名。

```sh
python3 tools/build-single.py
python3 tools/package.py
```

第一条生成 `dist/shanshui-courtyard-single.html`，可直接用浏览器打开，无需 HTTP 服务或联网。
第二条会自动重建单文件，再生成 `dist/山水楼阁-Unity准备版.zip`，不需要预先创建 `dist`。
ZIP 包含 README、源码、模型、Blender/Unity 项目和离线预览；排除编辑器缓存与自动备份。

## 路径与验证

- Blender 脚本从脚本文件、已打开的项目 `.blend` 或当前工作目录寻找项目根目录。
  通过 MCP 执行代码片段时，先打开本项目的 `.blend`，或从项目根目录启动 Blender。
- `tests/browser/*.js` 是可由 Playwright 调用的异步函数，第二参数可传 `screenshotDir`；
  默认截图输出到运行目录下的 `tests/results/browser/screenshots/`。
  离线检查还需传 `singleFileUrl`（用 Node 的 `pathToFileURL` 从本机路径转换），结束后返回原页面。
- `tools/verify-unity-mcp.py --server PATH` 可指定本机 MCP 可执行文件；不传时自动查找。
  MCP 是可选的编辑器自动化工具，浏览器预览与离线打包不依赖它。
- 可运行不依赖 Unity、Blender 或第三方 Python 包的回归检查：

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

这些检查覆盖干净副本打包、中文与空格路径、异地工作目录、旧预览重建和路径解析，
不能代替 Unity 编译或 Play Mode 验收。

## 开发规范与检查

开发与提交流程见 [参与开发](CONTRIBUTING.md)，目录、代码、资产和坐标契约见 [项目规范](docs/project-standards.md)，运行端验收见 [测试说明](docs/testing.md)。自动化助手还应遵守 [AGENTS.md](AGENTS.md)。

安装 Python 3.9+ 和 Node.js 24 后运行（Windows 可用 `python` 替代 `python3`）：

```sh
python3 tools/check-project.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

GitHub Actions 在 Linux、Windows 执行基础检查；Unity 编译、Play Mode 和 Windows 游戏构建需另行实测。
