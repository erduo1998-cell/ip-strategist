# ip-strategist

> 実際の悩みを AI の IP コーチに渡す。まず判断、次に完成物、最後に検証できる一歩だけを残します。

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![Version 2.0.0](https://img.shields.io/badge/version-2.0.0-286A51?style=flat-square)](VERSION) [![skills.sh](https://img.shields.io/badge/skills.sh-ip--strategist-BBD96B?style=flat-square)](https://skills.sh/erduo1998-cell/ip-strategist) [![CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-E26D4A?style=flat-square)](LICENSE) [![Tests 108](https://img.shields.io/badge/tests-108%20checks-286A51?style=flat-square)](https://github.com/erduo1998-cell/ip-strategist/actions)

**Codex、Claude Code、そのほか Agent Skills 対応ホストで利用できます。** 自然言語が共通入口です。対応ホストでは `/ip-strategist` も使えます。

[30 秒で開始](#30-秒で開始) · [デモ](#一つの実際の質問が結果になるまで) · [七つのタスク](#七つのタスク) · [インストール](#インストール) · [更新](#更新) · [ライセンス](#ライセンスと商用許可)

![クリエイターと AI の IP コーチが現在の判断に集中し、複雑な方法論は背後に整理されている](assets/ip-strategist-hero.webp)

## 先に使い方を学ぶ必要はありません

今どこで詰まっているかを、そのまま伝えてください。`ip-strategist` は会話から主タスクを一つ選び、タスクカプセルを一つだけ読み、完成物まで返します。深い方法論を参照するのは、判断の衝突や根拠の説明が必要なときだけです。

| 実際の状況 | 得られるもの |
| --- | --- |
| ツールと経営の話が混在し、何者か覚えてもらえない | ポジショニング、対象者、コンテンツ柱、人物像の境界 |
| 曖昧なアイデアがあり、公開する価値を判断できない | 作る／修正して作る／作らないの判断と実行可能なテーマ |
| 方向性を 60 秒の話し言葉にしたい | 最小限のテーマ検証、完成台本、表現意図 |
| 再生は多いのにプロフィール閲覧とフォローが少ない | 原因判断と、変数を一つだけ変える次バッチ |
| 保存は多いのに相談・成約がない | 振り返り、再現する型、検証基準、収益化への接続 |
| 会話を変えるたびに過去の判断が失われる | 私的記録、途中再開、判断契約、継続レビュー |

## 30 秒で開始

```bash
# 読み取りだけ。ホストには書き込まない
npx -y skills add erduo1998-cell/ip-strategist --list

# Codex のみにインストール
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

Claude Code では `codex` を `claude-code` に変更します。`--all` は検出された全 Agent に書き込むため、既定では使いません。

新しいセッションで、実際のタスクを直接入力します。

```text
企業向け AI コンサルをしていますが、内容がツールと経営の話を行き来しています。
ポジショニング、対象者、3 本のコンテンツ柱を作り直してください。
```

情報が足りればすぐ納品します。答えを変える事実が不足するときだけ、重要な質問を一つします。

## 一つの実際の質問が結果になるまで

以下は**架空データのデモ**です。「12 万再生なのにフォローは 80、なぜ？」という入力から、成長カプセルだけを選び、判断と次の施策を返します。

[![架空デモ：実際の質問が統一入口に入り、成長カプセルだけを読み、判断と次の施策を返す](assets/ip-strategist-demo.gif)](assets/ip-strategist-demo.mp4)

[高解像度 MP4](assets/ip-strategist-demo.mp4) を開けます。アニメーションはリポジトリ内の [Remotion ソース](demo/remotion/)から決定的にレンダリングされ、実在の顧客、アカウント、実績を示しません。

## 七つのタスク

| 完了したい仕事 | 代表的な入力 | 納品物 |
| --- | --- | --- |
| <!-- capability:positioning --> **ポジショニングと人物像** | 経歴、事業、対象者の迷い | ポジショニング、対象者、柱、境界 |
| <!-- capability:topic --> **テーマを探す・選ぶ・磨く** | 方向、トレンド、曖昧な案 | 取捨選択、需要判断、最終テーマ |
| <!-- capability:script --> **アイデアをコンテンツにする** | テーマ、素材、途中原稿 | 構成、話し言葉台本、表現意図 |
| <!-- capability:growth --> **立ち上げ・成長・シリーズ化** | アカウント症状、投稿結果 | 成長診断、記憶資産、シリーズ、実験 |
| <!-- capability:review --> **公開済み内容を振り返る** | 投稿、再生、反応、転換 | 帰属判断、変数診断、次バッチ |
| <!-- capability:monetization --> **収益化を設計する** | 事業、商品、価格、見込み客 | 収益化経路、内容接続、検証順序 |
| <!-- capability:onboarding --> **長期伴走を続ける** | 目標、経歴、既存記録 | 初期診断、契約、途中再開、振り返り |

## 巨大なプロンプトではない理由

![実際の依頼が一つの入口と一つの現行タスクカプセルを通り、納品後のフィードバックで改めて判断される](assets/workflow-map.svg)

- 一つの入口。利用者は内部の機能一覧を学びません。
- 通常タスクは `SKILL.md + 一つの task-*` だけを読み、`references/00-11` を既定で通読しません。
- クイックモードは記録を作らず、私的状態を読みません。伴走時も現在タスクの要約だけを使います。
- 深層方法論は削除されていません。答えを変える判断、動作、品質基準だけをカプセル化しています。

## 検証可能なリリース基準

`SKILL.md` 7,799 bytes、最大既定経路 14,299 bytes、既定カプセル 1 個、状態要約 6,000 bytes 以下、自動テスト 108 件実行（任意のオンライン比較 1 件をスキップ）、隔離した完成物テスト 11 クラス、公開言語 5 種。

## インストール

対象ホストを限定する推奨コマンド：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g \
  --agent codex --skill ip-strategist -y
```

CLI が検出した全 Agent へ明示的に入れたい場合だけ `-g --all` を使います。

Git 互換インストール：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git \
  ~/.claude/skills/ip-strategist
```

## 更新

Agent に次のように伝えます。

```text
更新 ip-strategist
```

`scripts/ip-update.py` は公式リポジトリだけを受け付けます。誤った remote、ローカル変更、私的状態、fast-forward 不可なら停止します。Git の手動手順：

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

## 私的状態と v1 互換性

v2 は v1.9 の `ip-dossier.md`、`ip-contracts/`、七つの機械フィールドと互換です。再作成や schema 更新は不要です。私的状態は利用者の作業ディレクトリに置き、Skill の設置先には置きません。

## 対応範囲

本 Skill は IP の位置づけ、コンテンツ判断、ショット意図、文案を扱います。編集、広告、チーム、配信、アカウント操作は実行しません。資格、数値、事例、成果、提携、収益を捏造しません。高影響分野ではコンテンツ戦略のみを提供します。

## ライセンスと商用許可

**v2.0.0** 以降は [CC BY-NC 4.0](LICENSE) です。共有・改変には表示、ライセンスへのリンク、変更表示が必要で、商用利用には別途書面許可が必要です。

これは**非商用利用に限るソース公開**プロジェクトで、商用利用を認める OSI オープンソースではありません。MIT で既に取得した v1 の権利は維持され、v2 は遡及して取り消しません。[NOTICE.md](NOTICE.md) と [SUPPORT.md](SUPPORT.md) を参照してください。

## 作者に連絡

<p align="center">
  <img src="assets/wechat-qrcode.jpg" alt="耳総の WeChat QR コード" width="220"><br>
  <strong>劉冉 / 耳総</strong><br>
  AI コンサルタント · 元映像ディレクター · オープン Agent ツール実践者<br>
  WeChat でスキャンし「ip-strategist」と記載<br>
  <a href="https://github.com/erduo1998-cell">GitHub</a> · <a href="https://erduo.art">erduo.art</a>
</p>

1対1 IP コンサルティングと商用利用許可は別契約です。範囲と要件は [SUPPORT.md](SUPPORT.md) を参照してください。

## 保守と貢献

[変更履歴](CHANGELOG.md) · [仕様](SPEC.md) · [トラブルシューティング](TROUBLESHOOTING.md) · [貢献](CONTRIBUTING.md) · [架空対話](docs/示例对话.md) · [ビジュアル由来](assets/visual-provenance.md)

私的記録、顧客データ、認証情報を issue、PR、fixture に入れないでください。
