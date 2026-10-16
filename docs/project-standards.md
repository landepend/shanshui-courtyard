# 项目规范

## 项目边界与目录职责

Unity 是 Windows 游戏主工程；浏览器提供可离线运行的模型展示与漫游预览。两端分别验收，浏览器通过不能证明 Unity 玩法已完成。

| 路径 | 职责与修改约定 |
| --- | --- |
| `unity/` | 游戏代码、编辑器工具、运行资源与工程配置 |
| `blender/` | 可编辑源模型与可复核建模脚本 |
| `assets/` | 跨引擎 GLB 和设定参考；模型同步的源文件 |
| `src/`、`index.html` | 浏览器原生模块与界面 |
| `vendor/` | 固定版本第三方 JavaScript 与许可证 |
| `tools/` | 检查、同步、构建和打包工具 |
| `tests/browser/` | 接收 Playwright `page` 的浏览器验收函数 |
| `tests/test_*.py` | 可独立运行的标准库单元测试 |
| `tests/results/`、`docs/screenshots/` | 有日期与环境说明的验证证据；既有记录仅代表当时结果 |
| `docs/` | 坐标契约、设计说明、人工验收清单 |
| `archive/` | 历史版本，常规开发不修改 |
| `dist/` | 可重建的交付产物，不纳入 Git |

## 代码与文件约定

- 文本使用 UTF-8、LF、文件末尾换行；遵守根目录 `.editorconfig` 与 `.gitattributes`。新代码使用清晰分行，修改现有密集代码时只整理相关区域。
- JavaScript 新代码使用 2 空格、分号、单引号；变量和函数 `camelCase`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`。浏览器模块保持相对导入，Three.js 从本地 import map 加载。
- Python 新代码使用 4 空格、`snake_case`、标准库优先；可执行工具采用 `main()` 和入口保护。禁止依赖调用者工作目录，使用 `Path(__file__).resolve()` 定位资源。
- C# 使用 4 空格、`Shanshui` 命名空间、类型/方法/属性 `PascalCase`、字段/局部变量 `camelCase`。保留现有 Unity 序列化字段名，重命名时处理序列化迁移。Editor API 只放在 `Assets/Editor/` 或编辑器条件编译中。
- PowerShell 使用 4 空格、参数声明和 `$ErrorActionPreference = 'Stop'`；以 `$PSScriptRoot` 定位项目，涉及空格或中文路径时使用 `-LiteralPath`。
- 注释解释坐标、约束和设计原因。面向玩家的错误信息明确可见；资产加载失败不得被旧模型或静默降级掩盖。
- `src/scene.js` 管理场景、环境和界面；`architecture.js` 管理建筑载入、构件与灯光；`explore.js` 管理漫游；`character.js` 管理角色模型与动画。新逻辑放入职责最接近的模块。
- Unity 帧循环避免无必要分配、重复查找和无界扫描。性能改动记录测量设备、分辨率、场景、前后数据，不能仅凭静态检查宣称流畅。

## 资源与依赖

- `assets/architecture/courtyard.glb` 和 `assets/characters/atang.glb` 为共享模型基准；Unity `Assets/Art/` 的对应副本必须逐字节相同。
- Pages 发布使用 `tools/build-pages.py` 生成独立的 `dist/pages/`；为满足单文件 25 MiB 限制，建筑派生为 glTF 与多个本地 buffer，单个 buffer 不超过 16 MiB。该发布格式不替代共享 GLB，不引入远程资源；不得直接发布整个源码目录。
- GLB 使用 glTF 2.0，纹理和 buffer 内嵌，避免外部路径。保留角色 25 骨骼和九个动作：`Idle`、`Walk`、`Run`、`Sprint`、`Jump`、`Fall`、`Land`、`Climb`、`Glide`。更改契约必须同时更新消费者、检查和文档。
- 建筑保留 `roof`、`dougong`、`column`、`window`、`corridor` 五类 `extras.part` 标识，供真实几何点选使用。不得以对象命名猜测替代结构标识。
- 保留源 `.blend`、导出 GLB 和可复核脚本；修改模型时记录 Blender 版本、导出参数、网格/三角形数、文件大小和截图。历史脚本不要求批量重写。
- 普通 Git 保存当前资源，不在本次规范中自动迁移 Git LFS。新增或更新的单个资源超过 50 MiB 先说明必要性；达到 100 MiB 前采用 LFS 或外部发布方案并记录获取方式，禁止直接提交超限文件。
- Unity 资源移动与 `.meta` 一起处理；已存在的 GUID 不得重建。序列化场景和预制体使用文本模式，资产可见元文件由 Editor 管理。
- 浏览器依赖保持仓库内固定版本，升级时同步官方扩展和许可证并验收离线单文件。Unity 依赖使用明确版本或 Git commit；保留 Editor 生成的依赖锁文件，不使用浮动分支。
- 无法确认来源和授权的资源不得引入发布包；设定图来源与提示词保留记录。第三方许可证与项目自身授权分别处理。

## 坐标与玩法契约

设计与浏览器采用 `(x, 高度 y, z)`；Blender 网格采用 `(x, -z, y)`，glTF 导出恢复 Y 向上。Unity 世界采用 `Unity(x,y,z) = Three(x,y,-z)`；glTFast 的导入变换和建筑额外旋转见 [Unity 说明](../unity/README.txt)。

楼板、房门、楼梯与碰撞数据以 [迁移布局](unity-migration-layout.json) 为现有基准，建筑细节见 [模型说明](architecture-model.txt)。改变尺寸必须同时检查视觉模型、两端碰撞、出生点、镜头与路径；角色模型以脚底为原点。游戏距离使用米、速度使用米/秒，变量命名或注释明确单位。

## 验收与发布标准

基础检查覆盖源码语法、JSON、模型结构和资源同步；运行时效果按 [测试说明](testing.md) 验收。新增规则必须能在干净克隆中执行，且明确哪些验证需要外部 Editor 或浏览器。

验证记录说明提交、日期、执行环境、命令/步骤、通过项和未验证项。`tests/results/` 中旧记录不得自动当成当前验证。新浏览器截图和临时检查报告放入被忽略的目录，确需保存的证据由评审明确选取。

发布前确认源码提交、基础检查、离线预览及相关 Unity 验收完成；使用 `v主版本.次版本.修订版本` 标签并写明兼容性变化。未完成 Unity 构建的版本使用“准备版”或预发布标记，记录限制。源码、离线 HTML 与 Windows EXE 分别标明，发布包由同一源码快照重建。
