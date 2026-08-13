# ip-strategist

> 먼저 비공개 IP 기록을 만드세요. 이후 모든 질문은 기록과 데이터로 근본 원인과 증상을 구분한 뒤 완성물과 검증할 다음 한 단계를 냅니다.

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![Version 2.0.1](https://img.shields.io/badge/version-2.0.1-286A51?style=flat-square)](VERSION) [![skills.sh](https://img.shields.io/badge/skills.sh-ip--strategist-BBD96B?style=flat-square)](https://skills.sh/erduo1998-cell/ip-strategist) [![CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-E26D4A?style=flat-square)](LICENSE) [![Tests 115](https://img.shields.io/badge/tests-115%20checks-286A51?style=flat-square)](https://github.com/erduo1998-cell/ip-strategist/actions)

**Codex, Claude Code 및 Agent Skills를 지원하는 호스트에서 사용할 수 있습니다.** 자연어가 공통 입구이며, 지원 호스트에서는 `/ip-strategist`도 사용할 수 있습니다.

[30초 시작](#30초-시작) · [데모](#하나의-실제-질문이-결과가-되는-과정) · [일곱 가지 작업](#일곱-가지-작업) · [설치](#설치) · [업데이트](#업데이트) · [라이선스](#라이선스와-상업적-허가)

![크리에이터와 AI IP 코치가 현재 판단에 집중하고 복잡한 방법론은 뒤에서 정리되어 있는 모습](assets/ip-strategist-hero.webp)

## 사용법부터 배울 필요가 없습니다

첫 사용에서는 목표, 실제 경험과 근거, 대상, 가치, 사업, 실행 제약, 이후 데이터를 담는 여섯 부분의 비공개 기록을 만듭니다. 그 뒤에는 막힌 문제를 그대로 말하세요. `ip-strategist`는 관련 요약을 먼저 읽고, 사용자가 말한 문제가 근본 원인인지 증상인지 검증되지 않은 가설인지 증거와 충돌하는지 판단한 다음 작업 캡슐 하나로 결과를 만듭니다.

| 실제 상황 | 받게 되는 결과 |
| --- | --- |
| 도구와 경영 이야기가 섞여 무엇을 하는 사람인지 기억되지 않음 | 포지셔닝, 대상, 콘텐츠 축, 페르소나 경계 |
| 막연한 아이디어가 있지만 만들 가치가 있는지 모름 | 제작／수정 후 제작／보류 판단과 최종 주제 |
| 방향을 60초 구어체 대본으로 만들고 싶음 | 최소 주제 검증, 완성 대본, 표현 의도 |
| 조회수는 높지만 프로필 방문과 팔로우가 낮음 | 원인 판단과 변수 하나만 바꾸는 다음 묶음 |
| 저장은 많지만 문의와 매출이 없음 | 회고, 재현할 모형, 검증 기준, 수익 연결 |
| 대화를 바꿀 때마다 이전 판단이 사라짐 | 개인 기록, 중단점 재개, 판단 계약, 장기 회고 |

## 30초 시작

```bash
# 읽기 전용 확인. 호스트 디렉터리에 쓰지 않음
npx -y skills add erduo1998-cell/ip-strategist --list

# Codex에만 설치
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

Claude Code는 `codex`를 `claude-code`로 바꿉니다. `--all`은 감지된 모든 Agent에 쓰므로 기본값으로 사용하지 않습니다.

새 세션에서는 먼저 다음과 같이 입력합니다.

```text
ip-strategist를 처음 사용합니다. 비공개 IP 기록을 만들어 주세요.
```

Agent는 저장 위치와 개인정보 경계를 설명하고 동의를 한 번 받습니다. 그다음 여섯 모듈을 한 번에 한 질문씩 진행합니다. 완성 초안을 확인해 `provisional`이 되기 전에는 포지셔닝, 주제, 대본, 성장, 회고, 수익화를 처리하지 않습니다. 이후에는 작업과 새 데이터를 바로 주면 표면 증상을 진단으로 착각하지 않습니다.

## 하나의 실제 질문이 결과가 되는 과정

아래는 **가상 데이터 데모**입니다. “12만 조회인데 팔로우는 80명뿐인 이유?”라는 질문에 먼저 관련 기록과 데이터를 읽고, 표면 증상을 미래 가치에 대한 검증 가설로 다시 정의한 뒤 성장 캡슐을 선택합니다.

[![가상 데모: 실제 질문이 통합 입구로 들어가 성장 캡슐 하나만 불러 판단과 다음 행동을 전달하는 과정](assets/ip-strategist-demo.gif)](assets/ip-strategist-demo.mp4)

[고해상도 MP4](assets/ip-strategist-demo.mp4)를 열 수 있습니다. 애니메이션은 저장소의 [Remotion 소스](demo/remotion/)에서 결정적으로 렌더링되며 실제 고객, 계정 또는 성과를 나타내지 않습니다.

## 일곱 가지 작업

| 완료할 일 | 대표 입력 | 결과 |
| --- | --- | --- |
| <!-- capability:positioning --> **포지셔닝과 페르소나** | 경험, 사업, 대상 혼란 | 포지셔닝, 대상, 콘텐츠 축, 경계 |
| <!-- capability:topic --> **주제 찾기·판단하기·다듬기** | 방향, 트렌드, 막연한 주제 | 선택 판단, 수요 분석, 최종 주제 |
| <!-- capability:script --> **아이디어를 콘텐츠로 만들기** | 주제, 자료, 부분 원고 | 구조, 구어체 대본, 표현 의도 |
| <!-- capability:growth --> **계정 시작·성장·시리즈화** | 계정 현상과 게시 결과 | 성장 진단, 기억 자산, 시리즈, 실험 |
| <!-- capability:review --> **게시한 콘텐츠 회고** | 게시물, 조회, 반응, 전환 | 귀인, 변수 진단, 다음 행동 |
| <!-- capability:monetization --> **콘텐츠 수익화 설계** | 사업, 상품, 가격, 리드 | 수익 경로, 콘텐츠 연결, 검증 순서 |
| <!-- capability:onboarding --> **판단 기반 만들기** | 첫 사용, 중단점, 기록 누락 | 비공개 기록, 근거 장부, 재개, 회고 |

## 거대한 프롬프트가 아닌 이유

![실제 요청이 하나의 통합 입구와 현재 작업 캡슐 하나를 거치며 결과 전달 후 피드백에 따라 다시 판단되는 흐름](assets/workflow-map.svg)

- 기록이 먼저입니다. 첫 사용은 반드시 기록을 만들고, 완료 전 새 작업은 근거와 대기 작업으로 보존합니다.
- 매번 다시 진단합니다. 정식 작업은 관련 기록과 데이터 요약으로 근본 원인, 증상, 가설을 구분합니다.
- 하나의 입구이므로 사용자가 내부 기능 목록을 먼저 배울 필요가 없습니다.
- 정식 작업은 `SKILL.md + 작업별 상태 요약 + 하나의 task-*`만 읽고 `references/00-11`을 기본으로 통독하지 않습니다.
- 기록은 사용자 작업 디렉터리에만 둡니다. 거부하거나 안전한 읽기·쓰기가 불가능하면 낮은 신뢰도와 비저장을 명시한 제한 분석만 제공합니다.
- 심층 방법론은 삭제되지 않았습니다. 답을 바꾸는 판단, 행동, 품질 기준만 캡슐에 컴파일합니다.

## 검증 가능한 릴리스 기준

`SKILL.md` 9,225 bytes, 6,000-byte 상태 요약 상한을 포함한 최대 기본 경로 22,745 bytes, 기본 캡슐 1개, 상태 요약 6,000 bytes 이하, 자동 테스트 115개 실행(선택적 온라인 비교 1개 건너뜀), 격리된 결과 테스트 11종, 기록 우선 행동 테스트 4세션, 공개 언어 5개.

## 설치

권장하는 범위 지정 설치:

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

CLI가 감지한 모든 Agent에 설치하려는 경우에만 `-g --all`을 사용합니다.

Git 호환 설치:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git \
  ~/.claude/skills/ip-strategist
```

## 업데이트

Agent에게 다음과 같이 말합니다.

```text
更新 ip-strategist
```

`scripts/ip-update.py`는 공식 저장소만 허용합니다. 잘못된 remote, 로컬 변경, 개인 상태, fast-forward 불가 상태에서는 멈춥니다. Git 수동 절차:

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

## 개인 상태와 v1 호환성

v2는 v1.9의 `ip-dossier.md`, `ip-contracts/`, 일곱 개 계약 기계 필드와 호환됩니다. 기록 재생성이나 schema 변경이 필요 없습니다. 개인 상태는 사용자 작업 디렉터리에 두고 Skill 설치 경로에는 두지 않습니다.

## 범위

이 Skill은 IP 포지셔닝, 콘텐츠 판단, 샷 의도, 카피를 다룹니다. 편집, 광고, 팀, 라이브 방송, 계정 작업을 대신 수행하지 않습니다. 자격, 수치, 사례, 성과, 제휴, 수익을 꾸며내지 않습니다. 고영향 분야에서는 콘텐츠 전략만 제공합니다.

## 라이선스와 상업적 허가

**v2.0.0**부터 [CC BY-NC 4.0](LICENSE)을 사용합니다. 공유·개작에는 출처, 라이선스 링크, 변경 표시가 필요하며 상업적 사용에는 별도 서면 허가가 필요합니다.

이 프로젝트는 **비상업적 사용을 위한 소스 공개**이며 상업적 사용을 허용하는 OSI 오픈소스가 아닙니다. MIT로 이미 받은 v1 사본의 권리는 유지되며 v2가 소급 취소하지 않습니다. [NOTICE.md](NOTICE.md)와 [SUPPORT.md](SUPPORT.md)를 확인하세요.

## 저자에게 연락

<p align="center">
  <img src="assets/wechat-qrcode.jpg" alt="얼둬의 WeChat QR 코드" width="220"><br>
  <strong>류란 / 얼둬</strong><br>
  AI 컨설턴트 · 전 영상 감독 · 오픈 Agent 도구 실천가<br>
  WeChat에서 스캔 후 “ip-strategist”라고 적어 주세요<br>
  <a href="https://github.com/erduo1998-cell">GitHub</a> · <a href="https://erduo.art">erduo.art</a>
</p>

1:1 IP 컨설팅과 상업적 사용 허가는 별도입니다. 범위와 요건은 [SUPPORT.md](SUPPORT.md)를 확인하세요.

## 유지관리와 기여

[변경 기록](CHANGELOG.md) · [사양](SPEC.md) · [문제 해결](TROUBLESHOOTING.md) · [기여](CONTRIBUTING.md) · [가상 대화](docs/示例对话.md) · [시각 자료 출처](assets/visual-provenance.md)

개인 기록, 고객 데이터, 자격 증명을 issue, PR, fixture에 넣지 마세요.
