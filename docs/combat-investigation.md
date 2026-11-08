# 战斗机制调查（2026-11-08）

## 结论

当前证据支持“游戏包含可进一步调查的阵营、目标过滤、伤害及生命属性机制”。**不能据此断言玩家角色已经支持互相伤害或原生联网。** 尚未完成函数调用链反编译及双角色运行验证。

目标：`platform/steam/PBZ.exe`，498913272 字节，x86-64 PE。

SHA-256：`4415933ce33476f14c837abb61a1b60af8b78cd81783896501913a7aac69e423`。REA 的 inspect_artifact 与 open_binary 已记录此身份；发布目录未包含带本机路径的完整环境诊断。

## 静态观察

通过可打印字符串及 PE 地址映射发现：

| 机制 | 原始标识 | 调查用途 |
| --- | --- | --- |
| 阵营修改 | `SetFaction`, `RuntimeUpdateFaction` | 检查玩家阵营能否独立设置 |
| 阵营关系覆盖 | `SetFactionRelationOverride`, `ClearFactionRelationOverride` | 检查能否只让房间中的玩家相互敌对 |
| 目标过滤 | `FilterTargetsByFactionRelation`, `IsValidTargetFactionRelation` | 检查攻击是否在命中前排除了玩家 |
| 伤害入口 | `TakeDamage`, `BPI_TakeDamage` | 追踪碰撞到属性修改的实际路径 |
| 生命属性 | `GetHealthAttribute`, `HealthAttribute` | HUD 与权威生命状态的候选入口 |
| 玩家专用计算 | `DamageCalculator_PBZPlayerScaled`, `DamageCalculator_PBZPlayerNonLethal` | 检查玩家伤害缩放、不致死与死亡规则 |
| 玩家伤害倍率 | `FactionDamageMultipliersWithPlayer` | 检查是否存在针对玩家的额外规则 |

二进制还保留以下开发时源码路径后缀；它们是字符串线索，不表示本机有这些源码：

- `Plugins/Secret/SGameCombatSystem/Source/SGameCombatSystem/Private/Faction/FactionComponent.cpp`
- `Plugins/AkashaEffects/Source/AkashaEffects/Private/Damage/CharAttackCollision.cpp`
- `Source/ProjectPBZ/System/Player/PBZPlayerController.cpp`

## 可追踪的注册候选

下面的入口是字符串旁的函数指针候选，尚未通过反汇编确认其角色。一个名字可能关联 UE 反射包装、元数据构造器等多个函数，不能直接把候选地址拿去 Hook。

| 名称 | 字符串 VA | 候选函数 VA |
| --- | --- | --- |
| SetFactionRelationOverride | `0x14bd22910` | `0x145e5cd50` |
| SetFaction | `0x14bd22768` | `0x145e5ccb0` |
| FilterTargetsByFactionRelation | `0x14bd22700` | `0x145e5bcb0` |
| IsValidTargetFactionRelation | `0x14bd14878` | `0x145e50d50` |
| GetFactionRelation | `0x14bd22460` | `0x145e5c1a0`, `0x145e5c240` |
| TakeDamage | `0x14bcca130` | `0x145df2630` |
| GetHealthAttribute | `0x14bccc5f8` | `0x145df0870` |

完整原始指针引用见 `evidence/native-registration-candidates.json`。地址按 PE 首选映像基址计算；运行时存在 ASLR，需使用 RVA 和实际模块基址重新定位。

## 已做和未做

- 已检查现有 UE4SS：有通用 SplitScreenMod 示例，但处于禁用状态；不是游戏多角色可用的证据。
- retoc 直接列主 utoc 失败：缺少加密密钥。**没有完成资源包解包。**
- 已克隆用户指定的 REA 仓库，commit `d72021b0dabedcc6fbc7bc6e0286fd359c604271`。
- 使用 REA CLI 6.7.0 完成 PE 静态身份检查，并经独立 stdio 会话打开 Ghidra 后端。
- Ghidra 12.1.4 已启动导入和自动分析，但该次会话结束前未取得 search_strings 的最终响应，也未取得函数伪代码。日志尾部有 PDB 未找到记录，这本身不等于分析失败原因；终止原因未确认。
- 尚未验证多玩家生成、伤害、格挡/弹反、锁定、受击、死亡、复活和网络复制。

## 必须查明的问题

1. 玩家攻击是否只扫描敌方通道，或硬编码排除玩家类？
2. 玩家目标关系设为敌对后，近战、投射物、范围伤害是否都能命中？
3. 玩家专用伤害计算器是否有单机全局玩家、强制不死或剧情状态依赖？
4. 输入、相机、锁定和控制器是否使用玩家 0 单例？
5. 命中停顿、慢动作、处决和弹反是否影响全局时间？
6. 原生网络设施是否实际承载了游戏状态复制？二进制中的 NetDriver、Steam/EOS 名字不足以证明这一点。
