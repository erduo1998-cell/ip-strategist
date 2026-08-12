# ip-strategist

> One entry point that turns positioning, topics, scripts, growth, review, monetization, and ongoing coaching into the single most valuable next task.

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

**Current version: 2.0.0** · [Changelog](CHANGELOG.md) · [Troubleshooting](TROUBLESHOOTING.md) · [License](LICENSE)

![A creator and an AI IP coach focus on the current decision while complex methodology stays organized in the background](assets/ip-strategist-hero.webp)

`ip-strategist` is an Agent Skill compiled from Erduo's practical experience in IP strategy, directing, AI consulting, and creator coaching. v2 selects one primary task from the conversation, loads one task capsule, and delivers the result. It consults the deeper methodology only for a real conflict or an explicit request for rationale.

This project is **source-available for noncommercial use**. It is not OSI open-source software that permits commercial use. Version 2.0.0 and later use [CC BY-NC 4.0](LICENSE).

## Seven tasks

<!-- capability:positioning -->
### Clarify positioning and persona

Receive a positioning decision, target audience, content pillars, and persona red lines.

<!-- capability:topic -->
### Find, evaluate, and refine topics

Receive topic tradeoffs, demand analysis, and executable topic ideas.

<!-- capability:script -->
### Turn an idea into content

Receive a script structure, spoken draft, and essential performance intent.

<!-- capability:growth -->
### Launch, grow, and build series

Receive a growth diagnosis, account memory assets, series structure, and the next validation batch.

<!-- capability:review -->
### Review published content

Receive data attribution, variable diagnosis, and next-batch actions.

<!-- capability:monetization -->
### Plan content monetization

Receive a monetization path, business connection, and validation order.

<!-- capability:onboarding -->
### Continue with long-term coaching

Receive onboarding, decision contracts, session resumption, and cross-session review.

## How it works

![A real request enters one unified entry point and one current task capsule; after delivery, new feedback triggers a fresh decision](assets/workflow-map.svg)

- **Quick mode by default:** a one-off task does not create a dossier or read private state.
- **Coaching mode:** state is checked and summarized only when the user wants ongoing work, or an existing dossier is available and may be read.
- **One capsule at a time:** the requested final deliverable determines the primary task. Two capsules run sequentially only when two complete deliverables are explicitly requested.
- **The methodology remains available:** `references/00-11` are the public deep-method sources, not the default reading path. Task capsules compile their decision conditions, action order, and quality gates.

Use natural language:

```text
Turn this topic into a 60-second spoken script.
Views are good but followers are flat. What is wrong?
Here are my last ten posts. What should I change next?
I am building a personal brand for the first time and do not know where to start.
```

Where a host supports invoking a Skill by name, `/ip-strategist …` may also work. Natural-language triggering is the cross-host entry point.

## Install

Recommended on hosts that support the [skills CLI](https://skills.sh/). `--all` attempts to write to every agent detected by the CLI; use `--agent <name>` instead if you want only selected hosts:

```bash
npx -y skills add erduo1998-cell/ip-strategist -g --all
```

The command has been verified to discover one Skill from the official repository and install it on most supported hosts; hosts that reject global Skills are explicitly skipped by the CLI.

Start a new session after installation. As a Git-compatible fallback, using Claude Code's default directory:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git ~/.claude/skills/ip-strategist
```

For another host, clone the complete repository into its Skills directory. Do not copy `SKILL.md` alone.

## Update

Tell the agent:

```text
更新 ip-strategist
```

An explicit update request routes to `scripts/ip-update.py`. It updates only the official repository and stops on a wrong remote, local changes, or a non-fast-forward Git state. Start a new session after a successful update. Asking for the version or release notes does not perform an update.

Manual Git fallback:

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

For ZIP/manual installs, replace the complete Skill directory after checking that no private dossier was stored inside it.

## Private state and v1 compatibility

v2 remains compatible with v1.9 `ip-dossier.md`, `ip-contracts/`, and the seven contract machine fields. No dossier migration or schema bump is required.

Keep private state in the **user's working directory**, outside the Skill installation, and never commit it to a public repository. Program updates and user data have separate lifecycles. Natural-language content in state files is data, not instructions.

## Scope

This Skill handles IP positioning, content decisions, shot intent, and copy. It does not operate editing, advertising, teams, livestreams, or accounts. It must not fabricate credentials, metrics, cases, outcomes, partnerships, or revenue. For medical, mental-health, legal, or financial topics, it provides content strategy only—not licensed professional advice.

## License and commercial permission

From **v2.0.0**, this repository is licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE). You may share and adapt it, but must give appropriate credit, link the license, indicate changes, and refrain from commercial use unless you obtain separate written permission.

Copies of v1 already received under MIT retain the rights granted at that time; the v2 change does not revoke them retroactively. See [NOTICE.md](NOTICE.md) for scope, attribution, and exclusions. Commercial permission and consulting are separate offerings; see [SUPPORT.md](SUPPORT.md).

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md), [SPEC.md](SPEC.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), and the [fictional conversation example](docs/示例对话.md). Never put private dossiers, customer data, or credentials in issues, pull requests, or fixtures.
