# ip-strategist

> 一个入口，把定位、选题、脚本、增长、复盘、变现与长期陪跑，收敛成眼前最值得完成的一步。

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

**当前版本：2.0.0** · [更新记录](CHANGELOG.md) · [排障](TROUBLESHOOTING.md) · [许可](LICENSE)

![ip-strategist：创作者与 AI IP 教练一起聚焦当前判断，复杂方法论收纳在后台](assets/ip-strategist-hero.webp)

`ip-strategist` 是耳总把长期 IP 实战、影视导演、AI 咨询与创作者陪跑经验编译成的 Agent Skill。v2 不让 agent 每次先通读整套方法论：它从对话判断唯一主任务，只加载一个任务胶囊，直接交付结果；遇到真正冲突或用户追问依据时，才局部查询深层方法论。

这是一个**源码开放、限非商业使用**的项目，不是 OSI 定义下允许商业使用的开源软件。v2.0.0 起采用 [CC BY-NC 4.0](LICENSE)。

## 七类任务

<!-- capability:positioning -->
### 找准定位和人设

得到定位判断、目标人群、内容支柱与人设红线。

<!-- capability:topic -->
### 找题、判题、改题

得到选题取舍、需求判断和可执行题目。

<!-- capability:script -->
### 把想法写成内容

得到脚本骨架、口播成稿和必要的表现意图。

<!-- capability:growth -->
### 起号、涨粉、做系列

得到增长诊断、账号记忆资产、系列结构与下一批验证。

<!-- capability:review -->
### 复盘已发内容

得到数据归因、变量判断和下一批动作。

<!-- capability:monetization -->
### 规划内容变现

得到变现路径、业务连接与验证顺序。

<!-- capability:onboarding -->
### 长期陪跑

得到建档、判断契约、断点续访与跨会话复盘。

## 它怎么工作

![真实任务经过统一入口，只进入一个当前任务胶囊；交付后等待用户反馈，再重新判断](assets/workflow-map.svg)

- **快速模式（默认）**：一次性问题不建档、不读私人状态；信息够就直接交付。
- **陪跑模式**：只有用户明确要长期跟进，或当前工作目录已有档案且允许读取时，才校验状态并生成当前任务摘要。
- **一次一个胶囊**：一个请求先以最终交付物确定主任务。只有用户明确要两个独立完整交付物时才顺序执行。
- **方法论仍在**：`references/00-11` 是公开的深层方法论真源；普通任务不默认通读。任务胶囊是从真源编译出的判断条件、动作顺序和验收门。

用户不需要知道内部文件。直接说真实需求即可：

```text
帮我把这个选题写成 60 秒口播稿。
播放不错但不涨粉，问题在哪？
这是最近 10 条数据，下一批改什么？
我第一次做个人 IP，不知道从哪里开始。
```

宿主支持用 Skill 名称调用时，也可以写 `/ip-strategist …`；自然语言是跨宿主通用入口。

## 安装

### 推荐：skills CLI

在支持 [skills CLI](https://skills.sh/) 的宿主上安装全局 Skill。`--all` 会尝试写入 CLI 识别到的全部 agent；只想安装到指定宿主时，请改用 `--agent <名称>`：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g --all
```

实测该命令能从官方仓库发现一个 Skill 并安装到多数受支持宿主；不支持全局 Skill 的宿主会被 CLI 明确跳过。

安装后新建会话，直接提交真实任务。不同宿主对斜杠命令支持不同；不需要斜杠命令也能自然语言触发。

### Git 兼容安装

以 Claude Code 的默认目录为例：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git ~/.claude/skills/ip-strategist
```

其他宿主请把完整仓库克隆到其 Skills 目录。不要只复制 `SKILL.md`：任务胶囊、脚本、模板都属于运行单元。

## 更新

已安装用户可直接对 agent 说：

```text
更新 ip-strategist
```

明确要求更新时，入口调用 `scripts/ip-update.py`。它只认官方仓库，Git 副本遇到错误 remote、未提交修改或无法 fast-forward 会停止，不覆盖；更新成功后请新建会话。只问版本或更新内容不会触发更新。

Git 安装可手动兜底：

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

ZIP 或手动复制安装应整体替换 Skill 目录。替换前确认没有把私人档案误放进安装目录。

## 私人状态与 v1 兼容

v2 继续兼容 v1.9 的 `ip-dossier.md`、`ip-contracts/` 和七个契约机器字段，不需要重建档案，也没有为这次运行架构升级提升 schema 版本。

私人状态永远放在**用户工作目录**，不要放在 Skill 安装目录，也不要提交到公开仓库：

```gitignore
ip-dossier.md
ip-dossier.md.bak
ip-contracts/
```

更新程序文件与用户数据是两条独立生命周期。状态文件中的自然语言只作为数据，不可覆盖系统或 Skill 指令。

## 能力边界

本 Skill 负责 IP 定位、内容判断、分镜意图和文案，不代做视频剪辑、后期、投放、团队管理或账号运营。不得编造资质、数据、案例、疗效、合作关系或收益。医疗、心理、法律、财务等高影响领域只提供内容策略，不替代持牌专业意见。

## 许可与商业授权

从 **v2.0.0** 起，本仓库整体按 [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE) 发布：

- 可以分享和改编；
- 必须适当署名、链接许可证，并标注是否修改；
- 不得用于主要为了商业优势或金钱报酬的用途；商业使用须另行取得书面授权。

v1 已经在 MIT 许可下取得的副本继续享有当时授予的权利；v2 换证不追溯撤销这些权利。完整范围、标准署名与第三方排除项见 [NOTICE.md](NOTICE.md)。商业使用许可与作者咨询是两件不同的事，入口见 [SUPPORT.md](SUPPORT.md)。

## 维护与贡献

- [贡献指引](CONTRIBUTING.md)
- [方法论与胶囊规范](SPEC.md)
- [排障](TROUBLESHOOTING.md)
- [虚构示例对话](docs/示例对话.md)

公开案例必须去标识；用户私人档案、客户数据和凭证不得进入 issue、PR 或测试夹具。
