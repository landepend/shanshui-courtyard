山水楼阁 · Unity 主项目准备版

状态：已准备源代码、依赖、资产同步与 Windows 构建入口。
本机尚未安装 Unity Editor，尚未经过 Unity 编译、Play Mode 或 Windows EXE 验证。
这不是已完成的 Windows 游戏构建。

1. Unity Hub 中安装 Unity 6 LTS 与 Windows Build Support。
2. 通过 Hub Add Project 添加当前 unity 文件夹。当前 ProjectVersion.txt 记录 6000.6.5f1；请按该版本导入，若主动改用其他版本，由 Editor 更新准确版本。
3. 等待 Package Manager 完成依赖导入：
   MCP for Unity 10.3.0，固定提交 aa5fc638d623f56178d50329d9ad8c541a57fe66。
   Unity 官方 glTFast 6.19.0（要求Unity6000.0或更新），用于本地GLB的编辑器导入。
4. 在项目根目录 PowerShell 运行：
   .\tools\sync-unity-assets.ps1 -RequireArchitecture
5. 编辑器菜单：山水楼阁 → 生成庭院主场景；成功后按Play。
   菜单：山水楼阁 → 构建 Windows 游戏；输出到项目 dist\windows\ShanshuiCourtyard.exe。

MCP配置
此前 Windows 环境已注册 unity stdio 服务；此注册不会随项目复制到其他电脑。
可选工具 python3 tools/verify-unity-mcp.py 自动查找 PATH、Unix bin 或 Windows Scripts 中的服务，也可传 --server 路径。
运行该工具的 Python 环境需要 mcp 包；缺失时会给出提示，不会改写旧验证记录。
Unity打开本项目后：Window → MCP for Unity → Transport选择Stdio → Start Session。
无需重新点击配置所有客户端，以免覆盖现有Codex条目。
服务握手验证：tests/results/unity-mcp-verification.json。
该文件区分MCP服务可用与Unity编辑器连接，当前实例数量为0。

坐标与资源
canonical模型是Three的Y向上右手系；玩法世界采用Unity(x,y,z)=Three(x,y,-z)。
glTFast默认反转X，因此建筑实例在世界中额外绕Y旋转180度。
角色GLB为局部资产，glTFast默认保留+Z正面，无额外世界旋转。
所有房间、阶梯、桥的坐标来源：../docs/unity-migration-layout.json。
Architecture layer9只用于精细相机遮挡与点选；角色身体与简化楼板/墙柱/平滑阶梯碰撞。
不以旧程序化建筑冒充新GLB。缺失建筑或角色时会显示明确提示，构建入口会拒绝继续。

键位
WASD/方向键移动；Shift奔跑；Ctrl冲刺；Space跳跃/空中开伞；E攀爬；X松手；鼠标拖动视角；滚轮缩放。
右下方按钮切换白昼/黄昏/夜景、正面/鸟瞰、继续漫游和回到入口。

官方来源
https://github.com/CoplayDev/unity-mcp/releases/tag/v10.3.0
https://github.com/CoplayDev/unity-mcp/tree/aa5fc638d623f56178d50329d9ad8c541a57fe66
https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.19/manual/ImportEditor.html
https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.19/manual/UpgradeGuides.html
https://developers.openai.com/codex/mcp/
