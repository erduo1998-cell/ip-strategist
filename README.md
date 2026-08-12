# ip-strategist

> 把你的真实问题交给 AI IP 教练：先给判断，再给成品，最后只留下一个能验证的下一步。

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

<p>
  <a href="VERSION"><img alt="Version 2.0.0" src="https://img.shields.io/badge/version-2.0.0-286A51?style=flat-square"></a>
  <a href="https://skills.sh/erduo1998-cell/ip-strategist"><img alt="skills.sh" src="https://img.shields.io/badge/skills.sh-ip--strategist-BBD96B?style=flat-square"></a>
  <a href="LICENSE"><img alt="CC BY-NC 4.0" src="https://img.shields.io/badge/license-CC%20BY--NC%204.0-E26D4A?style=flat-square"></a>
  <a href="https://github.com/erduo1998-cell/ip-strategist/actions"><img alt="Tests 108" src="https://img.shields.io/badge/tests-108%20checks-286A51?style=flat-square"></a>
</p>

**支持 Codex、Claude Code，以及其他支持 Agent Skills 的宿主。** 自然语言是通用入口；宿主支持时也可以使用 `/ip-strategist`。

[30 秒开始](#30-秒开始) · [看演示](#一条真实问题怎么变成结果) · [七类任务](#七类任务) · [安装](#安装) · [更新](#更新) · [许可](#许可与商业授权)

![ip-strategist：创作者与 AI IP 教练一起聚焦当前判断，复杂方法论收纳在后台](assets/ip-strategist-hero.webp)

## 你不需要先学会怎么用它

直接说你现在卡在哪。`ip-strategist` 会从对话里判断唯一主任务，只加载一个任务胶囊，直接完成交付；只有遇到真实冲突或你追问依据时，才局部查询深层方法论。

| 你现在的真实处境 | 它会交付什么 |
| --- | --- |
| 内容一会讲工具、一会讲管理，别人记不住你 | 一句话定位、目标人群、内容支柱与红线 |
| 有一个模糊想法，不知道值不值得拍 | 做 / 改后做 / 不做的判断，以及最终可拍题目 |
| 想把方向直接做成 60 秒口播 | 最小选题校验、完整成稿与表现意图 |
| 播放很高，但主页访问和涨粉很低 | 归因判断、只改一个变量的下一批方案 |
| 收藏不少，却没有咨询和成交 | 数据复盘、母版选择、验证标准与变现承接 |
| 每次换个对话，之前的判断都丢了 | 私有档案、断点续访、判断契约与跨会话复盘 |

## 30 秒开始

### 1. 安装到你正在使用的 Agent

先查看可安装的 Skill，不写任何宿主目录：

```bash
npx -y skills add erduo1998-cell/ip-strategist --list
```

只安装到 Codex：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

Claude Code 把 `codex` 改成 `claude-code`。不要默认使用 `--all`：它会写入 CLI 检测到的所有 Agent。

### 2. 新建会话，直接交任务

```text
我做企业 AI 咨询，但内容一会讲工具一会讲管理。
帮我重新做定位、目标人群和 3 个内容支柱。
```

信息够就直接给结果；只有缺少会改变判断的事实时，才追问一个关键问题。

### 3. 把结果或新事实继续交回来

```text
我按这个定位发了 6 条，第二类内容咨询最多。
下一批只改什么？
```

它会根据新证据重新判断当前一步，不自动安排一条漫长流程。

## 一条真实问题怎么变成结果

下面是一个**虚构数据演示**：用户只提交“播放 12 万，为什么只涨了 80 个粉？”，入口选择增长胶囊，给出核心判断和下一批动作。

[![虚构演示：真实问题进入统一入口，只加载增长胶囊，然后交付判断和下一批动作](assets/ip-strategist-demo.gif)](assets/ip-strategist-demo.mp4)

点击动画可打开 [高清 MP4](assets/ip-strategist-demo.mp4)。演示由 [Remotion 源码](demo/remotion/)确定性渲染；数据不对应真实客户、账号或业绩。

## 七类任务

| 你要完成的工作 | 常见输入 | 你会得到 |
| --- | --- | --- |
| <!-- capability:positioning --> **找准定位和人设** | 经历、业务、受众困惑 | 定位判断、目标人群、内容支柱与人设红线 |
| <!-- capability:topic --> **找题、判题、改题** | 一个方向、热点或模糊题目 | 选题取舍、需求判断和最终可拍题目 |
| <!-- capability:script --> **把想法写成内容** | 题目、素材或半成品 | 脚本骨架、口播成稿和表现意图 |
| <!-- capability:growth --> **起号、涨粉、做系列** | 账号现象、主页和内容表现 | 增长诊断、记忆资产、系列结构与下一批实验 |
| <!-- capability:review --> **复盘已发内容** | 内容样本、播放、互动和转化 | 数据归因、变量判断和下一批动作 |
| <!-- capability:monetization --> **规划内容变现** | 业务、产品、客单价和线索 | 变现路径、内容承接和验证顺序 |
| <!-- capability:onboarding --> **长期陪跑** | 目标、经历和已有档案 | 建档、判断契约、断点续访与跨会话复盘 |

熟悉后可以在同一入口后加意图词：

```text
/ip-strategist 选题：这个题值不值得做？
/ip-strategist 写稿：把这个方向写成 60 秒口播稿。
/ip-strategist 增长：播放不错但不涨粉，问题在哪？
/ip-strategist 陪跑：继续上次建档，不要从头问。
```

这些是同一个 Skill 的路由提示，不是七个需要分别安装的 Skill。

## 为什么它不是一篇巨型提示词

![真实任务经过统一入口，只进入一个当前任务胶囊；交付后等待用户反馈，再重新判断](assets/workflow-map.svg)

- **一个入口**：用户不需要先研究内部能力目录。
- **一个当前任务**：最终交付物决定唯一主路由；明确要求两个独立成品时才顺序执行。
- **一个胶囊**：普通任务只加载 `SKILL.md + 一个 task-*`，不默认通读 `references/00-11`。
- **快速模式默认**：一次性问题不建档、不读取私人状态。
- **陪跑状态有界**：只在用户明确长期跟进时读取任务相关摘要，需要复盘才打开被点名的单个契约。
- **方法论没有删除**：深层原件仍公开保留，胶囊只编译会改变答案的判断、动作和质量门。

## 可复核的发布门

| 项目 | v2.0.0 结果 |
| --- | ---: |
| `SKILL.md` | 7,799 bytes |
| 最大默认任务路径 | 14,299 bytes |
| 默认加载胶囊 | 1 个 |
| 状态摘要上限 | 6,000 bytes |
| 自动化测试 | 108 项运行，1 项可选在线比对跳过 |
| 隔离成品门 | 11 类真实任务通过 |
| 公开语言 | 简中、英语、日语、韩语、繁中 |

这些数字约束上下文负担，不冒充成品质量；定位、选题、写稿、增长、复盘、变现和建档还分别经过互不共享上下文的干净 Agent 测试。

## 安装

### skills CLI（推荐）

指定宿主安装，避免误写其他 Agent：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

常用 Agent 名：`codex`、`claude-code`。先用 `--list` 只读确认仓库中只有一个 `ip-strategist` Skill。

如果你明确希望写入 CLI 检测到的全部 Agent，才使用：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g --all
```

### Git 兼容安装

以 Claude Code 为例：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git \
  ~/.claude/skills/ip-strategist
```

其他宿主请把完整仓库克隆到其 Skills 目录。不要只复制 `SKILL.md`：任务胶囊、脚本和模板都属于运行单元。

## 更新

已安装用户直接对 Agent 说：

```text
更新 ip-strategist
```

入口会调用 `scripts/ip-update.py`。它只接受官方仓库；遇到错误 remote、本地修改、私人状态或无法 fast-forward 时会停止，不会强行覆盖。成功后请新建会话。

Git 安装的手动兜底：

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

ZIP 或手动副本要整体替换，替换前先确认安装目录里没有私人档案或本地修改。

## 私人状态与 v1 兼容

v2 继续兼容 v1.9 的 `ip-dossier.md`、`ip-contracts/` 和七个契约机器字段，不需要重建档案，也没有提升 schema 版本。

私人状态放在**用户工作目录**，不要放在 Skill 安装目录，也不要提交到公开仓库：

```gitignore
ip-dossier.md
ip-dossier.md.bak
ip-contracts/
```

程序更新与用户数据是两条独立生命周期。状态文件中的自然语言只作为数据，不能覆盖系统或 Skill 指令。

## 能力边界

本 Skill 负责 IP 定位、内容判断、分镜意图和文案，不代做视频剪辑、投放、团队管理、直播或账号操作。不得编造资质、数据、案例、疗效、合作关系或收益。医疗、心理、法律、财务等高影响领域只提供内容策略，不替代持牌专业意见。

## 许可与商业授权

从 **v2.0.0** 起，本仓库整体按 [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE) 发布：可以分享和改编，但必须适当署名、链接许可证、标注修改，且不得用于主要为了商业优势或金钱报酬的用途。商业使用须另行取得书面授权。

这是**源码开放、限非商业使用**的项目，不是 OSI 定义下允许商业使用的开源软件。v1 已经在 MIT 许可下取得的副本继续享有当时权利；v2 换证不追溯撤销。完整范围、标准署名与第三方排除项见 [NOTICE.md](NOTICE.md)，商业授权入口见 [SUPPORT.md](SUPPORT.md)。

## 联系作者

<p align="center">
  <img src="assets/wechat-qrcode.jpg" alt="耳总微信二维码" width="220"><br>
  <strong>刘冉 / 耳总</strong><br>
  AI 咨询顾问 · 前影视导演 · 开源 Agent 工具实践者<br>
  微信扫码添加，备注「ip-strategist」<br>
  <a href="https://github.com/erduo1998-cell">GitHub</a> · <a href="https://erduo.art">erduo.art</a>
</p>

1v1 IP 咨询与商业使用许可彼此独立；服务范围与授权要求见 [SUPPORT.md](SUPPORT.md)。

## 维护与贡献

- [更新记录](CHANGELOG.md)
- [方法论与胶囊规范](SPEC.md)
- [排障](TROUBLESHOOTING.md)
- [贡献指引](CONTRIBUTING.md)
- [虚构示例对话](docs/示例对话.md)
- [视觉与动画来源](assets/visual-provenance.md)

公开案例必须去标识；用户私人档案、客户数据和凭证不得进入 issue、PR 或测试夹具。
