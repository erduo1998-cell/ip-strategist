# ip-strategist

> 포지셔닝, 주제, 대본, 성장, 회고, 수익화, 장기 코칭을 하나의 입구에서 지금 가장 가치 있는 한 가지 작업으로 좁힙니다.

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

**현재 버전: 2.0.0** · [변경 기록](CHANGELOG.md) · [문제 해결](TROUBLESHOOTING.md) · [라이선스](LICENSE)

![크리에이터와 AI IP 코치가 현재 판단에 집중하고 복잡한 방법론은 뒤에서 정리되어 있는 모습](assets/ip-strategist-hero.webp)

`ip-strategist`는 耳总의 IP 실무, 영상 연출, AI 컨설팅, 크리에이터 코칭 경험을 컴파일한 Agent Skill입니다. v2는 대화에서 주 작업 하나를 고르고 작업 캡슐 하나만 읽어 결과를 바로 전달합니다. 실제 판단 충돌이나 근거 설명이 필요할 때만 심층 방법론을 조회합니다.

이 프로젝트는 **비상업적 사용을 위한 소스 공개** 프로젝트이며 상업적 사용을 허용하는 OSI 오픈 소스 소프트웨어가 아닙니다. v2.0.0부터 [CC BY-NC 4.0](LICENSE)을 적용합니다.

## 일곱 가지 작업

<!-- capability:positioning -->
### 포지셔닝과 페르소나 정하기

포지셔닝 판단, 타깃 사용자, 콘텐츠 기둥, 페르소나 금지선을 받습니다.

<!-- capability:topic -->
### 주제 찾기·판단하기·다듬기

주제 선택, 수요 판단, 실행 가능한 주제를 받습니다.

<!-- capability:script -->
### 아이디어를 콘텐츠로 만들기

대본 구조, 구어체 원고, 필요한 퍼포먼스 의도를 받습니다.

<!-- capability:growth -->
### 계정 시작·성장·시리즈 만들기

성장 진단, 계정 기억 자산, 시리즈 구조, 다음 검증 묶음을 받습니다.

<!-- capability:review -->
### 게시한 콘텐츠 회고하기

데이터 귀인, 변수 판단, 다음 실행을 받습니다.

<!-- capability:monetization -->
### 콘텐츠 수익화 설계하기

수익화 경로, 비즈니스 연결, 검증 순서를 받습니다.

<!-- capability:onboarding -->
### 장기 코칭 이어가기

초기 기록, 판단 계약, 중단 지점 재개, 세션 간 회고를 받습니다.

## 작동 방식

![실제 요청이 하나의 통합 입구와 현재 작업 캡슐 하나를 거치며 결과 전달 후 피드백에 따라 다시 판단되는 흐름](assets/workflow-map.svg)

- **기본은 빠른 모드:** 일회성 작업은 기록을 만들거나 개인 상태를 읽지 않습니다.
- **코칭 모드:** 장기 코칭을 원하거나 기존 기록 읽기가 허용된 경우에만 상태를 점검하고 작업 요약을 만듭니다.
- **한 번에 한 캡슐:** 최종 산출물이 주 작업을 결정합니다. 완전한 산출물 두 개를 명시한 경우에만 순서대로 처리합니다.
- **방법론은 유지:** `references/00-11`은 공개 심층 방법론 원본이며 일반 작업의 기본 읽기 경로가 아닙니다.

자연어로 실제 요청을 말하면 됩니다. 이름 호출을 지원하는 호스트에서는 `/ip-strategist …`도 사용할 수 있지만 자연어가 공통 입구입니다.

## 설치

[skills CLI](https://skills.sh/) 지원 호스트 권장 명령입니다. `--all`은 CLI가 감지한 모든 agent에 쓰기를 시도합니다. 일부 호스트만 원하면 `--agent <이름>`을 사용하세요:

```bash
npx -y skills add erduo1998-cell/ip-strategist -g --all
```

공식 저장소에서 Skill 하나를 찾고 대다수 지원 호스트에 설치되는 것을 확인했습니다. 글로벌 Skill을 지원하지 않는 호스트는 CLI가 명시적으로 건너뜁니다.

Git 호환 대안(Claude Code 기본 디렉터리 예시):

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git ~/.claude/skills/ip-strategist
```

전체 저장소를 설치하고 `SKILL.md`만 복사하지 마세요. 설치 후 새 세션을 시작하세요.

## 업데이트

Agent에게 다음과 같이 말하세요:

```text
更新 ip-strategist
```

명시적 업데이트 요청만 `scripts/ip-update.py`로 연결됩니다. 공식 저장소가 아니거나 로컬 변경이 있거나 fast-forward가 불가능하면 덮어쓰지 않고 중단합니다. 성공 후 새 세션을 시작하세요. 버전이나 변경 내용만 묻는 경우 업데이트하지 않습니다.

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

ZIP/수동 설치는 개인 기록이 설치 폴더에 없는지 확인한 뒤 Skill 디렉터리 전체를 교체하세요.

## 개인 상태와 v1 호환성

v2는 v1.9의 `ip-dossier.md`, `ip-contracts/`, 계약 기계 필드 일곱 개와 호환됩니다. 마이그레이션이나 schema 변경이 필요 없습니다. 개인 상태는 Skill 설치 밖의 **사용자 작업 디렉터리**에 두고 공개 저장소에 커밋하지 마세요. 상태 파일의 자연어는 데이터이지 지시가 아닙니다.

## 범위

이 Skill은 IP 포지셔닝, 콘텐츠 판단, 샷 의도와 카피를 담당합니다. 편집, 광고 집행, 팀, 라이브 방송, 계정 운영을 대신하지 않습니다. 자격, 수치, 사례, 효과, 제휴, 수익을 조작해서는 안 됩니다. 의료, 정신 건강, 법률, 금융 분야에서는 콘텐츠 전략만 제공하며 전문가 조언을 대체하지 않습니다.

## 라이선스와 상업적 허가

**v2.0.0**부터 [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)을 적용합니다. 공유와 개작은 가능하지만 적절한 저작자 표시, 라이선스 링크, 변경 표시가 필요하며 별도 서면 허가 없는 상업적 사용은 금지됩니다.

MIT로 이미 받은 v1 사본은 당시 권리를 유지하며 v2 변경으로 소급 취소되지 않습니다. 범위·표시·제외는 [NOTICE.md](NOTICE.md), 상업적 허가와 컨설팅의 별도 창구는 [SUPPORT.md](SUPPORT.md)를 확인하세요.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md), [SPEC.md](SPEC.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [가상 대화 예시](docs/示例对话.md)를 참조하세요. 개인 기록, 고객 데이터, 인증 정보를 issue, PR, fixture에 넣지 마세요.
