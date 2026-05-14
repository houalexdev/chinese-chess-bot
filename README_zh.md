# ♟️ AI 象棋大师争霸赛 — 四大 AI 同台竞技，谁主沉浮？

<p align="center">
  <a href="README.md">English</a> &nbsp;|&nbsp; 🌐 <strong>中文文档</strong>
</p>

> *把同一份提示词交给四个 AI，让它们各自写一个象棋引擎，然后互相厮杀——结果如何？*

本项目是一场运行在 [Botzone](https://botzone.org.cn) 平台上的**中国象棋 AI 大师赛**。四位 AI 选手各自持相同的精心设计的提示词，独立编写完整的 Python 象棋引擎，随后展开车轮大战。

---

## 🏆 最终排名

经过多轮循环对战，四位 AI 大师的战力排名如下：

| 排名 | 代号 | 模型 | 使用方式 | 代码行数 | Token 消耗 |
|------|------|------|----------|----------|------------|
| 🥇 第一 | **ccglm** | GLM-5.1 | Claude Code | 933 行 | ~178 万 |
| 🥈 第二 | **ccds** | DeepSeek V4 Pro | Claude Code | 1025 行 | ~630 万 |
| 🥉 第三 | **webds** | DeepSeek（网页版） | Web 对话 | 839 行 | — |
| 第四 | **webclaude** | Claude Sonnet 4.6 | Web 对话 | 967 行 | — |

> **备注：** Qwen 和 ChatGPT 也接受了相同的挑战，但均未能生成可实际对战的象棋程序。

---

## 🎬 终极决战：ccglm vs ccds

**冠军 vs 亚军，巅峰对决。**

![Watch the Grand Final](https://raw.githubusercontent.com/houalexdev/chinese-chess-bot/main/grand_final.mp4)

---

## 🤖 四位参赛选手档案

### 🥇 ccglm — *沉默刺客*
**GLM-5.1 × Claude Code** | 933 行 | ~178 万 tokens

代码最为精简，却称霸擂台。GLM-5.1 以最少的 Token 写出了战力最强的引擎，用实力证明：代码量从不等于战斗力。

### 🥈 ccds — *苦学派宗师*
**DeepSeek V4 Pro × Claude Code** | 1025 行 | ~630 万 tokens

本次消耗 Token 最多的选手，耗资高达 630 万 Token。DeepSeek 的引擎注释详尽、思路严谨，是一位勤奋的象棋学者，只可惜以微弱差距屈居亚军。

### 🥉 webds — *黑马挑战者*
**DeepSeek 网页版 × 直接对话** | 839 行

无需 Agent 框架，仅凭网页对话就写出了令人惊艳的引擎。DeepSeek 网页版的超强编程能力可见一斑。

### 4️⃣ webclaude — *奠基人*
**Claude Sonnet 4.6 网页版 × 直接对话** | 967 行

这个项目的起点。Claude 网页版奠定了整套提示词框架，也启发了 Claude Code 版本后来的突破。

---

## 🏗️ 技术架构

全部四个 Bot 均基于同一份主提示词独立实现：

```
📋 prompt.md  →  🤖 AI 模型  →  🐍 Python Bot  →  ⚔️ Botzone
```

### 引擎核心功能（提示词规范要求）

| 模块 | 说明 |
|------|------|
| **合法走法生成** | 覆盖全部 7 种棋子，含炮的隔子吃、马腿、象眼、九宫限制 |
| **搜索算法** | Alpha-Beta 剪枝 + PVS/NegaScout + 迭代加深 |
| **置换表** | Zobrist 哈希，≥100 万条目 |
| **走法排序** | 置换表最优走法 → MVV-LVA 吃子 → Killer 启发 → 历史启发 |
| **剪枝优化** | 空着剪枝 + 静态搜索（Quiescence Search） |
| **长打检测** | 长将/长捉检测（三次重复局面过滤） |
| **评估函数** | 棋子基础价值 + 10×9 位置加成表 + 机动性奖励 + 将军奖励 |
| **时间控制** | 软限制 3 秒停止加深，硬限制 4 秒立即返回（Botzone 限制 5 秒） |

### Botzone 输入输出协议

```json
// 输入（stdin）
{
  "requests":  [{"source": "-1", "target": "-1"}, {"source": "d9", "target": "d7"}],
  "responses": [{"source": "e2", "target": "e4"}]
}

// 输出（stdout）
{"response": {"source": "e3", "target": "e5"}}
```

坐标体系：列用字母 `a–i`（x = 0–8），行用数字 `0–9`（y=0 为红方底线）。

---

## 🚀 如何在 Botzone 上运行

1. 登录 [Botzone](https://botzone.org.cn)，创建新 Bot。
2. 语言选择 **Python 3**。
3. 将对应 `.py` 文件的内容完整粘贴进去。
4. 提交，等待对战。

无任何外部依赖，每个 Bot 均为单文件、开箱即用。

---

## 📁 项目结构

```
.
├── prompt.md          # 交给四位 AI 的统一主提示词
├── ccglm.py           # 🥇 GLM-5.1 × Claude Code
├── ccds.py            # 🥈 DeepSeek V4 Pro × Claude Code
├── webds.py           # 🥉 DeepSeek 网页版
├── webclaude.py       # 4️⃣ Claude Sonnet 4.6 网页版
├── assets/
│   └── grand_final.mp4  # （在此放入录屏视频）
└── README.md
```

---

## 💡 实验结论

- **Claude Code（Agent 模式）的代码质量稳定优于直接网页对话**，多轮迭代 + 工具调用的 Agentic 工作流对象棋引擎这类复杂任务有显著优势。
- **GLM-5.1 以最少 Token 取得最佳成绩**，性价比约为 DeepSeek V4 Pro 的 3.5 倍。
- **同一份提示词，四种截然不同的实现**——每个 AI 在走法排序、位置表设计、搜索调优上各有取舍。
- **Qwen 和 ChatGPT 无法通过同样的提示词生成可战程序**。

---

## 📜 开源许可

MIT — 欢迎 fork，用你自己的 AI 写一个更强的 Bot。

---

*一份提示词，四个 AI，一场象棋擂台赛。*
