# 分析方法与本机工具记录

## Python 静态调查

Python 3.8+，仅使用标准库，不运行游戏、不修改游戏文件。输入应是 PE32+ 的本次 PBZ 可执行文件；PE 指针脚本是针对该文件的研究脚本，不是通用的恶意文件解析器。

```powershell
python tools/scan_combat_strings.py --game-root 'D:\steam\steamapps\common\PBZ'
python tools/find_native_registration.py --game-root 'D:\steam\steamapps\common\PBZ'
```

默认输出到仓库 `.local/evidence`，不进入 Git。首个脚本保留可打印 ASCII 与 ASCII 子集 UTF-16LE 的匹配字符串和文件偏移。第二个读取 PE 段表，把字符串文件偏移转为首选映像 VA，再定位其绝对指针引用和相邻 qword。

相邻 qword 可能是反射注册包装器、元数据指针或别的结构；必须交叉引用与反汇编确认，不得当作已解析函数或可用 Hook 地址。

## REA

用户提供仓库：<https://github.com/AllToBeNize/rea>，调查时 HEAD 为 `d72021b0dabedcc6fbc7bc6e0286fd359c604271`。

本次实际执行使用 npm 发布包 `rea-agents@6.7.0`（未把 fork 源码构建为运行时）。Node 24.15.0 可以运行此版本。尝试 latest 时得到 6.8.0，其 Node 版本要求更高，故改为 6.7.0；没有升级本机 Node。

```powershell
npx -y rea-agents@6.7.0 doctor --client codex --json
npx -y rea-agents@6.7.0 inspect-artifact 'D:\steam\steamapps\common\PBZ\platform\steam\PBZ.exe' --json
```

Ghidra 使用官方 12.1.4 便携发行包，归档 SHA-256：`ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`。官方来源：<https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build>。

Java 复用本机 Rider 的 JBR 21（含 javac），只给分析子进程设置 JAVA_HOME、GHIDRA_INSTALL_DIR 等，没有修改全局环境或 Codex MCP 配置。工具包保留在游戏目录的 `PBZ_MultiplayerResearch/tools`，没有提交到本仓库。

后续可在独立 PowerShell 中给环境变量配置实际工具路径，然后用持久 stdio MCP 会话依次调用 open_binary(provider_id=ghidra)、search_strings、xrefs、analyze_function，并逐步保存 Evidence。关闭前执行 close_binary。需要扩展首轮分析时限时，使用 REA_GHIDRA_STARTUP_TIMEOUT_MS；本次设置为 1200000。

不要为每个函数启动一次全新的 Ghidra 导入。优先追踪 combat-investigation.md 的注册候选，确认 UE 包装函数及其真正调用的实现。完整游戏程序的自动分析成本较高，客户端会话生命周期必须覆盖分析过程。本次导入启动但没有完成可用的函数级结果。

## UE 资源包

已有 retoc 的 list 命令读取 ProjectPBZ-Windows.utoc 返回缺少加密密钥。未完成解密、资源解包或蓝图导出。需要先取得适用本版本且有权使用的解包配置，再定向检查玩家类、阵营数据、攻击碰撞、伤害计算和地图资产。REA 原生分析不自动解决 UE IoStore 解密。

## 本版验证

- C++20 接口使用 MSVC 14.44.35207 `/Zs /TP /std:c++20` 语法检查通过；仅说明声明合法，未验证网络行为。
- Python 脚本在本次本机游戏程序上实际运行，候选结果可复现。
- 未运行游戏 PvP 或任何联网测试。
