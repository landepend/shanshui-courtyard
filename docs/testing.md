# 检查与验收

## 基础检查

在项目根目录执行，Python 3.9+ 与 Node.js 24 即可，无需安装 npm 包：

```sh
python3 tools/check-project.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

`check-project.py` 解析当前 Python、JavaScript 与 JSON，验证两份 GLB 的结构、角色骨骼/动作、建筑构件标识和 Unity 副本一致性。它不启动 Blender、Unity 或浏览器。Node 缺失时检查失败并提示安装，不静默跳过。

GitHub Actions 的 `Project checks` 在 Linux 和 Windows 执行基础检查，另外在 Linux 构建离线 HTML；两端还通过 PowerShell 7 执行 C# 语法检查。静态解析不验证 Unity API、导入器或真实渲染。首次建立工作流后可由维护者将两个系统的 `Checks` 设为分支保护必需检查。

## 按变更范围验收

| 改动 | 必要补充验证 |
| --- | --- |
| 文档、协作配置 | 相对链接、命令可执行性、差异检查 |
| 浏览器代码或界面 | 本地预览、相关浏览器 QA、控制台错误、离线单文件 |
| 角色或建筑资源 | 模型结构、Unity 哈希同步、Blender 画面、两端导入与相关漫游路径 |
| Unity C# 或配置 | C# 语法、Editor 编译、Play Mode、相关人工验收项 |
| 打包与路径工具 | 单元测试、中文/空格路径、离线单文件、交付包内容 |
| 正式 Windows 发布 | 全部适用检查、Unity 构建、Windows 实机启动与玩法验收 |

## 浏览器验收

```sh
python3 start.py --no-browser --port 8000
python3 tools/build-single.py
```

在浏览器打开 `http://127.0.0.1:8000/`，检查建筑和阿棠载入、构件点选、昼夜与视角切换、WASD/奔跑、入口和楼梯、加载失败提示及恢复。再直接打开 `dist/shanshui-courtyard-single.html`，关闭网络验证模型、动画和交互。

`tests/browser/*-qa.js` 是供已有 Playwright 会话调用的异步函数表达式，不是可直接 `node` 运行的测试，也没有随仓库提供 Playwright runner。需使用可信本地测试环境提供 `page`。每个 QA 使用独立 page/context，避免监听器和路由相互影响。结果输出到 `tests/results/browser/`，截图目录由调用方预先创建。调用参数为：

```js
await qa(page, {
  screenshotDir: '/absolute/path/to/tests/results/browser/screenshots',
  singleFileUrl: pathToFileURL('/absolute/path/to/dist/shanshui-courtyard-single.html').href
});
```

单文件相关 QA 需要 `singleFileUrl`；其余 QA 使用已打开本地预览的 `page`。实际截图和帧率应注明设备、视口及测试场景。

## Pages 发布目录验收

```sh
python3 tools/build-pages.py
python3 -m http.server 8000 --directory dist/pages
```

在 `http://127.0.0.1:8000/` 执行浏览器验收，确认 `courtyard.gltf` 和各个本地 `.bin` 请求成功，
建筑与角色载入、五类构件和昼夜切换正常。加载失败测试需拦截发布模型的 `.gltf` 或 `.bin` URL，
源码预览仍拦截 `courtyard.glb`。单元测试检查逐个 buffer view 的字节与完整模型元数据不变、
中文/空格路径、异地工作目录、旧产物清理和文件上限；CI 在 Linux、Windows 构建 Pages 目录。
本地构建或浏览器通过不等于 Cloudflare 实际部署成功，远端结果需另行确认。

## Unity 验收

```sh
pwsh -NoProfile -File tools/sync-unity-assets.ps1 -RequireArchitecture
pwsh -NoProfile -File tools/check-unity-csharp-syntax.ps1
```

第二条使用 PowerShell 7 内置 Roslyn，仅检查 C# 语法，不等同于 Unity 编译。通过 Unity Hub 打开 `unity/`，等待导入，确认 Console 无编译错误，再执行“山水楼阁 → 生成庭院主场景”和 Play Mode。依据 [玩家验收清单](unity-player-qa.txt) 检查碰撞、上下楼、镜头、体力、攀爬、滑翔与落水恢复。

Windows 发布使用“山水楼阁 → 构建 Windows 游戏”，并在 Windows 实机启动 `dist/windows/ShanshuiCourtyard.exe` 验收。没有相应 Editor、模块或平台时，明确标记该项“未验证”。

`tools/verify-unity-mcp.py` 为可选的本地桥接检查，需要另行安装 MCP 服务及 Python `mcp` 包；不属于无依赖基础检查。MCP 握手成功与 Editor 连接成功分别记录，也不能替代编译或 Play Mode。
