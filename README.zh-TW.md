# ip-strategist

> 一個入口，把定位、選題、腳本、成長、復盤、變現與長期陪跑，收斂成眼前最值得完成的一步。

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

**目前版本：2.0.0** · [更新紀錄](CHANGELOG.md) · [疑難排解](TROUBLESHOOTING.md) · [授權](LICENSE)

![創作者與 AI IP 教練一起聚焦目前判斷，複雜方法論收納在後台](assets/ip-strategist-hero.webp)

`ip-strategist` 是耳總把長期 IP 實戰、影視導演、AI 諮詢與創作者陪跑經驗編譯成的 Agent Skill。v2 從對話判斷唯一主任務，只載入一個任務膠囊並直接交付結果；只有真正的判斷衝突或使用者追問依據時，才局部查詢深層方法論。

這是**原始碼公開、限非商業使用**的專案，不是 OSI 定義下允許商業使用的開源軟體。v2.0.0 起採用 [CC BY-NC 4.0](LICENSE)。

## 七類任務

<!-- capability:positioning -->
### 找準定位和人設

得到定位判斷、目標人群、內容支柱與人設紅線。

<!-- capability:topic -->
### 找題、判題、改題

得到選題取捨、需求判斷和可執行題目。

<!-- capability:script -->
### 把想法寫成內容

得到腳本骨架、口播成稿和必要的表現意圖。

<!-- capability:growth -->
### 起號、漲粉、做系列

得到成長診斷、帳號記憶資產、系列結構與下一批驗證。

<!-- capability:review -->
### 復盤已發內容

得到資料歸因、變數判斷和下一批動作。

<!-- capability:monetization -->
### 規劃內容變現

得到變現路徑、業務連結與驗證順序。

<!-- capability:onboarding -->
### 長期陪跑

得到建檔、判斷契約、斷點續訪與跨會話復盤。

## 運作方式

![真實任務經過統一入口，只進入一個目前任務膠囊；交付後等待使用者回饋，再重新判斷](assets/workflow-map.svg)

- **快速模式（預設）**：單次任務不建檔、不讀私人狀態；資訊足夠就直接交付。
- **陪跑模式**：只有使用者明確要長期跟進，或既有檔案可讀時，才檢查狀態並產生目前任務摘要。
- **一次一個膠囊**：最終交付物決定主任務。只有明確要求兩個獨立完整交付物時才依序執行。
- **方法論仍在**：`references/00-11` 是公開的深層方法論真源，不是普通任務的預設讀取路徑。

直接用自然語言提交真實需求。宿主支援用 Skill 名稱呼叫時也可使用 `/ip-strategist …`；自然語言是跨宿主通用入口。

## 安裝

支援 [skills CLI](https://skills.sh/) 的宿主建議使用。`--all` 會嘗試寫入 CLI 偵測到的全部 agent；只想安裝到指定宿主時，請改用 `--agent <名稱>`：

```bash
npx -y skills add erduo1998-cell/ip-strategist -g --all
```

實測該命令能從官方倉庫找到一個 Skill 並安裝到多數支援宿主；不支援全域 Skill 的宿主會由 CLI 明確略過。

Git 相容備援（以 Claude Code 預設目錄為例）：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/erduo1998-cell/ip-strategist.git ~/.claude/skills/ip-strategist
```

請安裝完整倉庫，不要只複製 `SKILL.md`。安裝後新建會話。

## 更新

對 agent 說：

```text
更新 ip-strategist
```

只有明確更新要求才會呼叫 `scripts/ip-update.py`。它只更新官方倉庫；遇到錯誤 remote、本機修改或無法 fast-forward 會停止，不會覆蓋。成功後請新建會話。只詢問版本或更新內容不會執行更新。

```bash
cd ~/.claude/skills/ip-strategist
git status --short
git pull --ff-only
```

ZIP／手動安裝應先確認安裝目錄沒有私人檔案，再整體替換 Skill 目錄。

## 私人狀態與 v1 相容

v2 相容 v1.9 的 `ip-dossier.md`、`ip-contracts/` 與七個契約機器欄位，不需重建檔案或提升 schema。私人狀態永遠放在 Skill 安裝目錄外的**使用者工作目錄**，不要提交到公開倉庫。狀態檔中的自然語言是資料，不是指令。

## 能力邊界

本 Skill 負責 IP 定位、內容判斷、分鏡意圖與文案，不代做剪輯、後期、投放、團隊、直播或帳號營運。不得捏造資格、資料、案例、療效、合作或收益。醫療、心理、法律、財務領域只提供內容策略，不取代持牌專業意見。

## 授權與商業許可

從 **v2.0.0** 起，本倉庫依 [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE) 發布。可以分享和改編，但必須適當署名、連結授權並標示修改；未另取得書面許可不得商業使用。

已依 MIT 取得的 v1 副本繼續享有當時授予的權利；v2 換證不追溯撤銷。範圍、標準署名與排除項見 [NOTICE.md](NOTICE.md)。商業使用許可與作者諮詢是兩件不同的事，入口見 [SUPPORT.md](SUPPORT.md)。

## 貢獻

參閱 [CONTRIBUTING.md](CONTRIBUTING.md)、[SPEC.md](SPEC.md)、[TROUBLESHOOTING.md](TROUBLESHOOTING.md) 與[虛構對話範例](docs/示例对话.md)。不要把私人檔案、客戶資料或憑證放入 issue、PR 或 fixture。
