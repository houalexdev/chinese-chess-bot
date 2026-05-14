# ♟️ AI Xiangqi Grand Masters — Four AIs Enter, One Reigns Supreme

<p align="center">
  🌐 <strong>English</strong> &nbsp;|&nbsp; <a href="README_zh.md">中文文档</a>
</p>

> *What happens when you hand four different AI systems the same chess prompt and make them fight?*

This project is a **Xiangqi (Chinese Chess) bot tournament** built for the [Botzone](https://botzone.org.cn) platform. Four AI systems — each given the same carefully engineered prompt — independently wrote their own complete chess engine in Python. Then they fought each other.

---

## 🏆 The Tournament Results

After multiple rounds of round-robin play, the final power ranking is:

| Rank | Codename | Model | Mode | Lines of Code | Token Cost |
|------|----------|-------|------|---------------|------------|
| 🥇 1st | **ccglm** | GLM-5.1 | Claude Code | 933 | ~1.78M |
| 🥈 2nd | **ccds** | DeepSeek V4 Pro | Claude Code | 1025 | ~6.3M |
| 🥉 3rd | **webds** | DeepSeek (Web) | Web Chat | 839 | — |
| 4th | **webclaude** | Claude Sonnet 4.6 | Web Chat | 967 | — |

> **Note:** Both Qwen and ChatGPT were also given the same prompt but failed to produce a functional, battle-ready bot.

---

## 🎬 The Grand Final: ccglm vs ccds

**Champion vs Runner-up — the ultimate clash.**

![Watch the Grand Final](https://raw.githubusercontent.com/houalexdev/chinese-chess-bot/main/grand_final.mp4)

---

## 🤖 The Four Competitors

### 🥇 ccglm — *The Silent Assassin*
**GLM-5.1 × Claude Code** | 933 lines | ~1.78M tokens

Compact, efficient, and deadly. GLM-5.1 produced the leanest codebase of the four yet dominated the tournament. Proof that token count doesn't equal strength.

### 🥈 ccds — *The Scholar*
**DeepSeek V4 Pro × Claude Code** | 1025 lines | ~6.3M tokens

The most expensive bot in the tournament at 6.3 million tokens. DeepSeek's engine is meticulous and deeply commented — a thorough student of the game that narrowly lost to its thriftier rival.

### 🥉 webds — *The Challenger*
**DeepSeek (Web) × Direct Chat** | 839 lines

The web chat version of DeepSeek produced a surprisingly strong engine with no agentic scaffolding — pure conversational code generation.

### 4️⃣ webclaude — *The Foundation*
**Claude Sonnet 4.6 × Direct Chat** | 967 lines

The baseline that inspired the project. Claude's web version laid the groundwork that the Claude Code variants ultimately surpassed.

---

## 🏗️ Technical Architecture

All four bots implement the same core chess engine specification from a single master prompt:

```
📋 prompt.md  →  🤖 AI Model  →  🐍 Python Bot  →  ⚔️ Botzone
```

### Engine Features (per the prompt spec)

| Module | Details |
|--------|---------|
| **Move Generation** | Full legal move gen for all 7 piece types, including cannon battery, blind horse leg, blind elephant eye, palace confinement |
| **Search** | Alpha-Beta with PVS/NegaScout, iterative deepening |
| **Transposition Table** | Zobrist hashing, ≥1M entries |
| **Move Ordering** | TT best move → MVV-LVA captures → Killer moves → History heuristic |
| **Pruning** | Null move pruning, quiescence search |
| **Repetition** | Long-check / long-chase detection (3-fold repetition filter) |
| **Evaluation** | Piece values + 10×9 positional tables + mobility bonus + check bonus |
| **Time Control** | Soft limit 3s, hard limit 4s (Botzone allows 5s per move) |

### Botzone I/O Protocol

```json
// Input (stdin)
{
  "requests":  [{"source": "-1", "target": "-1"}, {"source": "d9", "target": "d7"}],
  "responses": [{"source": "e2", "target": "e4"}]
}

// Output (stdout)
{"response": {"source": "e3", "target": "e5"}}
```

Coordinate system: columns `a–i` (x = 0–8), rows `0–9` (y = 0 is Red's back rank).

---

## 🚀 Running on Botzone

1. Log in to [Botzone](https://botzone.org.cn) and create a new bot.
2. Set language to **Python 3**.
3. Paste the contents of your chosen `.py` file.
4. Submit and let it fight.

No external dependencies — every bot is a single self-contained Python file.

---

## 📁 Repository Structure

```
.
├── prompt.md          # The master prompt given to all four AIs
├── ccglm.py           # 🥇 GLM-5.1 via Claude Code
├── ccds.py            # 🥈 DeepSeek V4 Pro via Claude Code
├── webds.py           # 🥉 DeepSeek Web Chat
├── webclaude.py       # 4️⃣ Claude Sonnet 4.6 Web Chat
├── assets/
│   └── grand_final.mp4  # (add your recording here)
└── README.md
```

---

## 💡 Key Findings

- **Agentic coding (Claude Code) consistently outperformed direct web chat**, suggesting iterative multi-turn code generation with tool use produces stronger engines.
- **GLM-5.1 achieved the best result with the fewest tokens** — 3.5× more efficient than DeepSeek V4 Pro for this task.
- **The same prompt, four wildly different implementations** — each AI had its own approach to move ordering, evaluation tables, and search tuning.
- **Qwen and ChatGPT could not produce a working bot** from the same prompt.

---

## 📜 License

MIT — use, fork, and let your own AI write a better bot.

---

*Built with curiosity, one prompt, and four competing AI systems.*
