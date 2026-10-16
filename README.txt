山水楼阁 · 阿棠行记
====================

主项目目录
项目根目录下的 unity 文件夹（路径随项目移动，不依赖原电脑盘符）

当前状态（2026-10-15）
用户已选择 Unity 作为 Windows 游戏主引擎，Godot 草稿保存于 archive/godot-draft。
Blender 建筑和新版动漫角色已制作并导出；Unity 代码、依赖、资源、MCP 已准备。
Unity Editor 尚未连接：目前没有完成 Unity 编译、Play Mode 测试或 Windows EXE 构建。
最后检查 Hub 主编辑器6000.6.5f1下载为failed/aborted，需在Hub检查恢复下载。
tests/results/unity-preparation.json 明确区分准备、编译、运行和构建状态。

首次打开 Unity
1. 在 Unity Hub 登录并安装 Unity 6 LTS Editor。
2. Hub → 项目 → 添加，选择本项目下的 unity 文件夹。
3. ProjectVersion.txt 已按当前 Hub 下载选择记录 6000.6.5f1。
   若随后更换版本，请在 Hub 使用实际安装版本打开项目，由 Editor 更新该文件。
4. 等待 Package Manager 安装已固定版本的 glTFast 和 MCP for Unity，完成 GLB 导入。
5. 菜单“山水楼阁 → 生成庭院主场景”，再点击 Play。
6. 菜单“山水楼阁 → 构建 Windows 游戏”，成功后输出到项目 dist/windows。
以上菜单尚待真正 Editor 验证，不能将脚本存在等同于游戏已运行。

MCP
CoplayDev/MCP for Unity v10.3.0，固定提交 aa5fc638d623f56178d50329d9ad8c541a57fe66。
本地 Python 服务已安装并注册到 Codex；初始化和48工具发现通过。
Editor 实例当前为0，需在 Unity 中打开本项目并启用 Window → MCP for Unity 的连接。
MCP 为本地编辑器桥接；云端图片、音频、模型生成工具已关闭。
许可证和具体安装参考：https://github.com/CoplayDev/unity-mcp
服务端验证记录：tests/results/unity-mcp-verification.json

资产和模型
assets/concepts/courtyard-atang-anime-v2.png：统一庭院/阿棠/纸鸢效果图
assets/concepts/courtyard-atang-anime-v2.prompt.txt：本次内置生图提示词
blender/Courtyard.blend：精细建筑源文件
blender/Atang_Anime_v3.blend：新版动漫角色源文件
assets/architecture/courtyard.glb：45网格、580864三角形、4080真实立体瓦片
assets/characters/atang.glb：角色、25骨骼、9动画、嵌入眼部纹理
角色动作：Idle Walk Run Sprint Jump Fall Land Climb Glide
参考原神的动漫造型和动作类型，保留阿棠原创汉服造型；并非原神角色或画质复刻。
本次3D建模通过本地 Blender MCP 完成，没有收费云端3D生成。
设定图使用了用户要求的内置图像生成。

Unity 操作设计（尚待 Play Mode 验证）
WASD移动，Shift奔跑，Ctrl冲刺，Space跳跃；空中Space展开/收起纸鸢。
E接近合法攀爬面开始攀爬，X松手/收翼。体力用于冲刺、攀爬、滑翔。
东南叠石望景台高4.58米，作为攀爬和滑翔测试区域。
拖动鼠标转动第三人称视角，滚轮调整距离，镜头避让墙体。
一层入口、室内楼梯及二层房间沿用原布局。
具体手动验收见 docs/unity-player-qa.txt。

文件分类
unity/                 Unity主项目：Assets、Packages、ProjectSettings
blender/scripts/       可复核的本地建模脚本（atang_v3和courtyard_v2为本次）
assets/                跨引擎原始模型和设定图
src/、index.html       浏览器预览版，保留原第三人称和房间探索
vendor/                Three.js 0.170.0及官方扩展、MIT许可证
docs/screenshots/      Blender渲染与浏览器验证截图
tests/results/         MCP、资产、语法和浏览器验证记录
tools/sync-unity-assets.ps1  将最新GLB复制到Unity并校验SHA256
tools/build-single.py  重建离线浏览器预览单文件
dist/                  预览与交付文件；尚无经过验证的Windows EXE
archive/               历史版本及已停止的Godot草稿

浏览器预览
在项目根目录运行 python start.py。
或者双击 dist/shanshui-courtyard-single.html；它包含模型与脚本，无需联网。
浏览器版可预览新版模型，但攀爬/滑翔主实现位于Unity，不能混同两者验收。
浏览器建筑加载、构件点选、昼夜/视角切换和失败提示/恢复已通过。
自动化浏览器采样只有6–9 FPS，不能据此宣称流畅，Unity实际性能仍待测。

