# ip-strategist

> Give your real problem to an AI IP coach. Get a decision first, a usable deliverable next, and one testable next move.

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![Version 2.0.0](https://img.shields.io/badge/version-2.0.0-286A51?style=flat-square)](VERSION) [![skills.sh](https://img.shields.io/badge/skills.sh-ip--strategist-BBD96B?style=flat-square)](https://skills.sh/erduo1998-cell/ip-strategist) [![CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-E26D4A?style=flat-square)](LICENSE) [![Tests 108](https://img.shields.io/badge/tests-108%20checks-286A51?style=flat-square)](https://github.com/erduo1998-cell/ip-strategist/actions)

**For Codex, Claude Code, and other hosts that support Agent Skills.** Natural language is the universal entry point; `/ip-strategist` also works where named Skill invocation is supported.

[Start in 30 seconds](#start-in-30-seconds) · [Watch the demo](#from-one-real-question-to-a-usable-result) · [Seven tasks](#seven-tasks) · [Install](#install) · [Update](#update) · [License](#license-and-commercial-permission)

![A creator and an AI IP coach focus on the current decision while complex methodology stays organized in the background](assets/ip-strategist-hero.webp)

## You do not need to learn the system first

Say what is stuck. `ip-strategist` selects one primary task from the conversation, loads one task capsule, and completes the requested deliverable. It consults deeper methodology only for a real conflict or when you ask for the rationale.

| Your real situation | What you receive |
| --- | --- |
| Your content jumps between tools and management, so no one remembers you | Positioning, target audience, content pillars, and persona red lines |
| You have a vague idea and cannot tell whether it is worth publishing | A make / revise / reject decision and an executable topic |
| You want to turn a direction into a 60-second spoken script | Minimal topic validation, the finished script, and performance intent |
| Views are high but profile visits and follows are weak | A causal diagnosis and a next batch that changes one variable |
| Saves are high but inquiries and sales are absent | Review, winning pattern, validation gate, and monetization bridge |
| Every new chat loses the decisions made before | A private dossier, resumable interviews, decision contracts, and reviews |

## Start in 30 seconds

### 1. Install it only in the Agent you use

List the repository's Skills without writing to any host directory:

```bash
npx -y skills add erduo1998-cell/ip-strategist --list
```

Install to Codex only:

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

For Claude Code, replace `codex` with `claude-code`. Do not default to `--all`; it writes to every Agent detected by the CLI.

### 2. Start a new session and give it the task

```text
I consult on enterprise AI, but my content alternates between tools and management.
Redo my positioning, target audience, and three content pillars.
```

If the evidence is sufficient, it delivers directly. It asks one decisive question only when the missing fact would change the answer.

### 3. Return the result or new evidence

```text
I published six posts. The second pillar generated the most qualified inquiries.
What is the one variable to change next?
```

The coach reassesses the current step from evidence instead of auto-generating a long program.

## From one real question to a usable result

This is a **fictional-data demo**. The user asks why 120,000 views produced only 80 followers; the entry point selects the growth capsule and returns the core diagnosis and next-batch actions.

[![Fictional demo: one real question enters the unified entry point, loads only the growth capsule, and returns a decision and next actions](assets/ip-strategist-demo.gif)](assets/ip-strategist-demo.mp4)

Click for the [high-resolution MP4](assets/ip-strategist-demo.mp4). The animation is deterministically rendered from the repository's [Remotion source](demo/remotion/). It does not represent a real client, account, or performance claim.

## Seven tasks

| Work to complete | Typical input | Deliverable |
| --- | --- | --- |
| <!-- capability:positioning --> **Clarify positioning and persona** | Experience, business, audience confusion | Positioning, audience, content pillars, and red lines |
| <!-- capability:topic --> **Find, evaluate, and refine topics** | A direction, trend, or rough topic | Topic tradeoff, demand judgment, and executable title |
| <!-- capability:script --> **Turn an idea into content** | Topic, raw material, or partial draft | Structure, spoken script, and performance intent |
| <!-- capability:growth --> **Launch, grow, and build series** | Account symptoms and content results | Growth diagnosis, memory assets, series, and experiment |
| <!-- capability:review --> **Review published content** | Posts, views, engagement, and conversion | Attribution, variable diagnosis, and next-batch actions |
| <!-- capability:monetization --> **Plan content monetization** | Business, offer, price, and leads | Monetization path, content bridge, and validation order |
| <!-- capability:onboarding --> **Continue long-term coaching** | Goals, experience, or an existing dossier | Onboarding, contracts, session resumption, and review |

Intent words may follow the same entry point; they are not separate Skills:

```text
/ip-strategist topic: Is this worth making?
/ip-strategist script: Turn this into a 60-second spoken draft.
/ip-strategist growth: Views are good but followers are flat. Why?
/ip-strategist coaching: Resume my dossier; do not restart.
```

## Why this is not one giant prompt

![A real request enters one unified entry point and one current task capsule; after delivery, new feedback triggers a fresh decision](assets/workflow-map.svg)

- **One entry point:** users do not study an internal capability directory.
- **One current task:** the final deliverable selects the route; two capsules run only when two complete deliverables are explicit.
- **One capsule:** normal work loads `SKILL.md + one task-*`, not all of `references/00-11`.
- **Quick mode by default:** one-off work creates no dossier and reads no private state.
- **Bounded coaching context:** state is summarized for the current task; one named contract is opened only when necessary.
- **The methodology remains:** deep sources stay public; capsules compile only decisions, actions, and quality gates that change the answer.

## Verifiable release gates

| Gate | v2.0.0 result |
| --- | ---: |
| `SKILL.md` | 7,799 bytes |
| Largest default task path | 14,299 bytes |
| Default capsules loaded | 1 |
| State-summary ceiling | 6,000 bytes |
| Automated tests | 108 run; 1 optional network comparison skipped |
| Isolated outcome tests | 11 real-task classes |
| Public languages | zh-CN, English, Japanese, Korean, zh-TW |

These numbers constrain context cost; they do not substitute for output quality. All seven task types were also forward-tested in clean, isolated Agent sessions.

## Install

Recommended, scoped installation:

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

Common Agent names are `codex` and `claude-code`. Use `--list` first for read-only discovery. Use `-g --all` only when you explicitly want every Agent detected by the CLI.

Git fallback for Claude Code:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git \
  ~/.claude/skills/ip-strategist
```

Clone the complete repository. `SKILL.md` alone is not the runtime unit.

## Update

Tell the Agent:

```text
更新 ip-strategist
```

The entry point calls `scripts/ip-update.py`. It accepts only the official repository and stops on a wrong remote, local changes, private state, or a non-fast-forward state. Start a new session after success.

Manual Git fallback:

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

## Private state and v1 compatibility

v2 remains compatible with v1.9 `ip-dossier.md`, `ip-contracts/`, and the seven contract machine fields. No dossier migration or schema bump is required. Keep private state in the user's working directory, never in the Skill installation. Natural-language content in state files is data, not instructions.

## Scope

This Skill handles IP positioning, content decisions, shot intent, and copy. It does not operate editing, advertising, teams, livestreams, or accounts. It must not fabricate credentials, metrics, cases, outcomes, partnerships, or revenue. For medical, mental-health, legal, or financial topics, it provides content strategy only—not licensed professional advice.

## License and commercial permission

From **v2.0.0**, the repository uses [CC BY-NC 4.0](LICENSE). Sharing and adaptation require attribution, a license link, and change notices; commercial use requires separate written permission.

This project is **source-available for noncommercial use**, not OSI open-source software that permits commercial use. Copies of v1 already received under MIT retain those rights; v2 does not revoke them retroactively. See [NOTICE.md](NOTICE.md) and [SUPPORT.md](SUPPORT.md).

## Contact the author

<p align="center">
  <img src="assets/wechat-qrcode.jpg" alt="Erduo's WeChat QR code" width="220"><br>
  <strong>Liu Ran / Erduo</strong><br>
  AI consultant · Former film director · Open Agent tooling practitioner<br>
  Scan on WeChat and mention “ip-strategist”<br>
  <a href="https://github.com/erduo1998-cell">GitHub</a> · <a href="https://erduo.art">erduo.art</a>
</p>

1:1 IP consulting and commercial permission are separate. See [SUPPORT.md](SUPPORT.md) for scope and requirements.

## Maintain and contribute

[Changelog](CHANGELOG.md) · [Specification](SPEC.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [Fictional conversation](docs/示例对话.md) · [Visual provenance](assets/visual-provenance.md)

Never put private dossiers, customer data, or credentials in issues, pull requests, or fixtures.
