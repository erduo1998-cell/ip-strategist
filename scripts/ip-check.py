#!/usr/bin/env python3
"""ip-strategist 状态一致性校验工具（零依赖，仅用 Python3 标准库）。

扫工作目录下的 ip-strategist 状态文件，报告三类问题：
  1. 契约状态一致性：过期待复盘、疑似漏回填实际发布日、状态非法值、
     状态-日期字段联动违规（含 已废弃 终态识别）。
  2. 档案 schema_version 与模板是否一致。
  3. 建档诊断状态/断点是否合法，已完成档案的核心字段是否齐全。
  4. 契约索引区（ip-dossier.md 里的只读表）与 ip-contracts/ 实际契约是否脱节。

零依赖原则：仅使用 Python3 标准库。PyYAML 是可选增强，若已安装则 frontmatter
解析更健壮（支持值内 `#`、多行字符串、YAML 列表）；未安装时回退手写解析器。

这不是必需工具，但解决「无校验脚本」的审查项——把 SKILL.md 启动协议里
「读档即比对」那条硬步骤交给一个能独立运行的检查器，避免人工漏看状态漂移。

用法:
  python3 scripts/ip-check.py [工作目录] [过期天数N]
  python3 scripts/ip-check.py [工作目录] [过期天数N] --sync-index

  工作目录   默认当前目录（.）。应含 ip-dossier.md 与 ip-contracts/。
  过期天数N  待发布契约预计发布日已过 N 天仍未回填实际发布日，报「疑似漏回填」。默认 3。

退出码:
  0  一切正常，或仅有「提醒」级问题（默认不阻断）。
  1  发现「警告」级问题。
  2  发现「错误」级问题。
  3  参数/路径错误或索引同步失败。
"""

import argparse
import datetime
import os
import re
import shutil
import sys
import tempfile

VALID_STATUS = ("待发布", "待复盘", "已复盘", "已废弃")
VALID_ONBOARDING_STATUS = ("in_progress", "provisional", "confirmed")
VALID_ONBOARDING_STEPS = (
    "goal", "evidence", "audience", "value", "business", "execution"
)

# v1.9 首次建档的最低可执行字段。标签与 dossier-template 一致，
# 便于在不引入额外 schema 依赖的情况下做确定性检查。
ONBOARDING_REQUIRED_FIELDS = (
    "为什么现在做 IP",
    "90 天唯一主要目标",
    "成功标准",
    "目标用户的具体状态",
    "用户的核心问题",
    "信任依据",
    "当前价值",
    "未来价值",
    "当前主行为",
    "变现方向或长期用途",
    "每周执行资源",
    "人设 / 伦理 / 隐私红线",
    "当前最大未知",
)

# 兼容旧模板/旧档案里可能写的别名，机器内部统一用 canonical 状态值。
STATUS_ALIASES = {
    "已废弃（已取消）": "已废弃",
}


def normalize_status(s):
    """把状态别名规范化为 canonical 值；未知/空值原样返回。"""
    if not s:
        return s
    return STATUS_ALIASES.get(s.strip(), s.strip())


# 保持零依赖：PyYAML 是可选增强；若用户环境未安装，则回退手写解析器。
try:
    import yaml
except ImportError:  # pragma: no cover - 标准环境无 PyYAML 时命中
    yaml = None
CONTRACT_ID_RE = re.compile(r"C-\d{8}-\d+")


# ---------------------------------------------------------------------------
# 通用解析
# ---------------------------------------------------------------------------

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def parse_frontmatter(text):
    """解析 YAML frontmatter（--- ... ---），返回 (key->value 字典, 解析错误信息)。

    优先尝试 PyYAML 解析（若已安装），以正确处理值内 `#`、多行字符串、YAML 列表。
    若 PyYAML 不存在或解析失败，回退手写解析器：只处理扁平 key: value，
    并剥离行内 `# 注释`。

    限制：手写回退不支持值内部含 `#` 的情况（如话题标签、URL fragment），
    模板 frontmatter 应避免在值内使用 `#`，或安装 PyYAML 获得完整兼容。

    返回:
        (dict, error_msg): dict 总是返回（无 frontmatter 返回 {}）；
        若 frontmatter 存在但无法解析，error_msg 为描述字符串，否则为 None。
    """
    if text is None:
        return {}, None
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, None

    # 切分出 frontmatter 区块（第一个 --- 到下一个 ---）
    lines = stripped.split("\n")
    if lines[0].strip() != "---":
        return {}, None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        # 有开头无结尾闭合：视为格式错误
        return {}, "frontmatter 未闭合（缺少结束 ---）"

    fm_text = "\n".join(lines[1:end])

    # 优先使用 PyYAML（可选依赖）
    if yaml is not None:
        try:
            parsed = yaml.safe_load(fm_text)
            if isinstance(parsed, dict):
                # 统一转字符串，保持与旧解析器下游接口一致
                result = {str(k): str(v) if v is not None else "" for k, v in parsed.items()}
                # schema_version 单独保留原始字符串，避免 PyYAML 把 1.10 解析成 1.1 后丢精度
                if "schema_version" in parsed:
                    raw_ver = _extract_raw_schema_version(fm_text)
                    if raw_ver is not None:
                        result["schema_version"] = raw_ver
                return result, None
            # 顶层不是映射，视为解析错误
            return {}, "frontmatter 顶层不是键值映射"
        except yaml.YAMLError as exc:
            # PyYAML 失败时，仍然回退手写解析器，但把错误带出来
            return _parse_frontmatter_fallback(fm_text, original_error=str(exc))

    return _parse_frontmatter_fallback(fm_text, original_error=None)


def _extract_raw_schema_version(fm_text):
    """从 frontmatter 原始文本中提取 schema_version 的字符串值（保留 1.10 等）。"""
    for line in fm_text.split("\n"):
        key, _, val = line.partition(":")
        if key.strip() == "schema_version":
            return val.strip().strip('"').strip("'")
    return None


def _parse_frontmatter_fallback(fm_text, original_error=None):
    """手写 frontmatter 回退解析器，保持零依赖。"""
    fm = {}
    has_error = original_error is not None
    for line in fm_text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if ":" not in line:
            # 非空行但不是键值对：手写解析器无法处理
            has_error = True
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        # 剥离行内注释：`value  # 注释` -> `value`
        # 限制：不支持值内包含 `#`，未来应改用真 YAML 解析器。
        val = re.sub(r"\s+#.*$", "", val).strip()
        val = val.strip().strip('"').strip("'").strip()
        if key:
            fm[key] = val
    error_msg = None
    if has_error:
        base = "frontmatter 解析异常"
        if original_error:
            base += "（PyYAML: %s）" % original_error
        error_msg = base
    return fm, error_msg


def parse_date(s):
    """解析 YYYY-MM-DD（或 YYYY/MM/DD，月/日允许 1-2 位），失败返回 None。"""
    if not s:
        return None
    s = s.strip().strip('"').strip("'").strip()
    # 先统一分隔符为 -
    normalized = re.sub(r"[/．.]", "-", s)
    parts = normalized.split("-")
    if len(parts) != 3:
        return None
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return datetime.date(year, month, day)
    except ValueError:
        return None


def parse_positive_int(s):
    """解析正整数，失败返回 None。"""
    if s is None or is_placeholder(str(s)):
        return None
    try:
        value = int(str(s).strip())
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def is_placeholder(v):
    """识别模板占位符或空值，不算真实值。"""
    if not v:
        return True
    v = v.strip()
    if not v:
        return True
    # 中文破折号、双横线、单横线、留空占位
    if v in ("—", "--", "-", "待填", "待诊断", "留空", "待定", "未知", "TBD"):
        return True
    unwrapped = v.strip("[]【】 ")
    if unwrapped in ("待填", "待诊断", "留空", "待定", "未知", "TBD"):
        return True
    return v.startswith("YYYY") or v.startswith("C-YYYYMMDD")


# ---------------------------------------------------------------------------
# 契约解析
# ---------------------------------------------------------------------------

def extract_title(text):
    """从契约正文 `- **选题标题**：xxx` 提取标题。"""
    if not text:
        return ""
    m = re.search(r"\*\*选题标题\*\*[：:]\s*(.+)", text)
    if not m:
        return ""
    line = m.group(1).strip()
    # 去掉行尾可能的说明括注 / markdown 残留
    line = re.split(r"[（(]", line)[0].strip()
    return line.strip("[]")


def parse_body_fields(text):
    """旧式契约（无 frontmatter）的正文加粗字段回退解析。"""
    if not text:
        return {}
    fields = {}
    patterns = {
        "contract_id": r"\*\*契约编号\*\*[：:]\s*(C-\d{8}-\d+)",
        # 正文回退同样支持四档状态（含已废弃）
        "status": r"\*\*状态\*\*[：:]\s*(待发布|待复盘|已复盘|已废弃（已取消）|已废弃)",
        "sign_date": r"\*\*签订日期\*\*[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        "plan_publish_date": r"\*\*预计发布日期\*\*[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        "actual_publish_date": r"\*\*实际发布日期\*\*[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        "review_after_days": r"\*\*发布后几天复盘\*\*[：:]\s*(\d+)",
        "next_review_date": r"\*\*下次复盘日\*\*[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            fields[key] = m.group(1).strip()
    return fields


# 契约头部 7 个 definitive 字段（状态机制的根）
DEFINITIVE_FIELDS = (
    ("contract_id", "编号"),
    ("status", "状态"),
    ("sign_date", "签订日期"),
    ("plan_publish_date", "预计发布日期"),
    ("actual_publish_date", "实际发布日期"),
    ("review_after_days", "发布后几天复盘"),
    ("next_review_date", "下次复盘日"),
)


def parse_contract(path):
    """解析一份契约，合并 frontmatter 与正文回退，返回字段字典。

    frontmatter 与正文回退合并规则：
      - 正文回退字段作为基础；
      - frontmatter 非空且非占位符的值覆盖正文；
      - frontmatter 中的占位符（如 C-YYYYMMDD-NN、YYYY-MM-DD 等）视为空，
        从而允许回退到正文或文件名。

    返回字典中可能包含：
      - frontmatter_error：frontmatter 存在但解析失败时的错误描述。
      - contract_id_conflict：frontmatter 编号与文件名不一致。
    """
    text = read_text(path)
    if text is None:
        return None
    fm, fm_error = parse_frontmatter(text)
    # 无论是否有 frontmatter，都读取正文回退字段；frontmatter 优先，正文作补充。
    body = parse_body_fields(text)
    merged = dict(body)
    for k, v in fm.items():
        # 空值与占位符都视为未填写，让正文/文件名回退生效。
        if v != "" and not is_placeholder(v):
            merged[k] = v

    # 状态值规范化：模板/旧档案可能写别名，机器内部用 canonical 值。
    raw_status = merged.get("status", "")
    if raw_status:
        merged["status"] = normalize_status(raw_status)
        merged["status_raw"] = raw_status.strip()

    if fm_error:
        merged["frontmatter_error"] = fm_error

    # contract_id：文件名永远是身份锚点
    fname = os.path.splitext(os.path.basename(path))[0]
    file_cid = fname if CONTRACT_ID_RE.fullmatch(fname) else None

    fm_cid = merged.get("contract_id", "")
    if is_placeholder(fm_cid):
        # frontmatter 还是模板占位符，以文件名为准，不报警告
        merged["contract_id"] = file_cid
    elif file_cid and fm_cid and fm_cid != file_cid:
        # 文件名与 frontmatter 编号不一致：记录冲突，但优先文件名
        merged["contract_id_conflict"] = (fm_cid, file_cid)
        merged["contract_id"] = file_cid
    elif not merged.get("contract_id") and file_cid:
        merged["contract_id"] = file_cid

    merged["title"] = extract_title(text)
    merged["path"] = path
    return merged


# ---------------------------------------------------------------------------
# Dossier 解析
# ---------------------------------------------------------------------------

def parse_schema_version(text):
    """从档案/模板取 schema_version：先 frontmatter，再正文正则。"""
    fm, _ = parse_frontmatter(text)
    if "schema_version" in fm:
        return fm["schema_version"]
    m = re.search(r"schema_version[：:\s]*\"?'?([0-9.]+)'?\"?", text or "")
    return m.group(1) if m else ""


def parse_markdown_bold_field(text, label):
    """读取 `**字段**：值` 的单行值；找不到返回空字符串。"""
    if not text:
        return ""
    pattern = r"^\*\*%s\*\*[\uff1a:]\s*(.*)$" % re.escape(label)
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def onboarding_missing_fields(text):
    """返回 v1.9 首次建档核心字段中缺失或仍为占位符的项。"""
    missing = []
    for label in ONBOARDING_REQUIRED_FIELDS:
        value = parse_markdown_bold_field(text, label)
        if is_placeholder(value):
            missing.append(label)
    return missing


def has_onboarding_evidence_row(text):
    """依据账本至少有一条非空结论，且标明状态、依据与验证。"""
    if not text or "### 依据账本" not in text:
        return False
    in_section = False
    for line in text.splitlines():
        if line.startswith("### 依据账本"):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("结论", "") or set(cells[0]) <= set("-: "):
            continue
        if cells[1] not in ("已确认事实", "暂定假设", "未知"):
            continue
        if all(not is_placeholder(cell) for cell in (cells[0], cells[2], cells[3])):
            return True
    return False


def parse_dossier_index(text):
    """解析 ip-dossier.md 的契约索引区表格，返回 {编号: {选题,状态,下次复盘日}}。"""
    index = {}
    if not text:
        return index
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and "编号" in s and "选题" in s:
            in_table = True
            continue
        if in_table:
            if not s.startswith("|"):
                break  # 表格结束
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 4:
                continue
            cid = cells[0]
            if set(cid) <= set("-: "):
                continue  # 分隔行
            if not CONTRACT_ID_RE.search(cid):
                continue
            m = CONTRACT_ID_RE.search(cid)
            cid = m.group(0)
            raw_status = cells[2]
            index[cid] = {
                "title": cells[1],
                "status": normalize_status(raw_status),
                "status_raw": raw_status,
                "next_review_date": cells[3],
            }
    return index


def render_dossier_index(contracts):
    """把契约原件渲染为 dossier 索引表。"""
    lines = [
        "| 编号 | 选题 | 状态 | 下次复盘日 |",
        "|------|------|------|----------|",
    ]
    for c in sorted(contracts, key=lambda item: item.get("contract_id", "")):
        cid = c.get("contract_id", "")
        if not cid:
            continue
        title = (c.get("title") or "未填写选题").replace("|", "／").strip()
        status = c.get("status") or "未填写"
        nrd = c.get("next_review_date") or ""
        if is_placeholder(nrd):
            nrd = ""
        lines.append("| %s | %s | %s | %s |" % (cid, title, status, nrd))
    if len(lines) == 2:
        lines.append("|  |  |  |  |")
    return "\n".join(lines)


def replace_dossier_index(text, contracts):
    """替换 dossier 的契约索引表；找不到标准索引区时抛 ValueError。"""
    lines = text.splitlines()
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## 二、契约索引区")),
        None,
    )
    if heading is None:
        raise ValueError("未找到“## 二、契约索引区”标题")

    table_start = None
    for i in range(heading + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if lines[i].strip().startswith("| 编号 |"):
            table_start = i
            break
    if table_start is None:
        raise ValueError("契约索引区内未找到标准表头")

    table_end = table_start
    while table_end < len(lines) and lines[table_end].strip().startswith("|"):
        table_end += 1

    replacement = render_dossier_index(contracts).splitlines()
    result = lines[:table_start] + replacement + lines[table_end:]
    return "\n".join(result) + ("\n" if text.endswith("\n") else "")


def sync_dossier_index(workdir):
    """从契约原件原子重建 dossier 索引，成功返回写入的契约数。"""
    dossier_path = os.path.join(workdir, "ip-dossier.md")
    contracts_dir = os.path.join(workdir, "ip-contracts")
    dossier_text = read_text(dossier_path)
    if dossier_text is None:
        raise ValueError("无法读取 ip-dossier.md")

    contracts = []
    if os.path.isdir(contracts_dir):
        for name in sorted(os.listdir(contracts_dir)):
            if name.startswith("C-") and name.endswith(".md"):
                contract = parse_contract(os.path.join(contracts_dir, name))
                if contract is not None:
                    contracts.append(contract)

    updated = replace_dossier_index(dossier_text, contracts)
    if updated == dossier_text:
        return len(contracts)

    backup_path = dossier_path + ".bak"
    shutil.copy2(dossier_path, backup_path)
    fd, temp_path = tempfile.mkstemp(
        prefix=".ip-dossier-", suffix=".tmp", dir=os.path.dirname(dossier_path)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(updated)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, dossier_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    return len(contracts)


def find_template_dossier(workdir, skill_dir=None):
    """定位模板档案：优先 skill_dir，其次脚本所在目录，最后工作目录。"""
    candidates = []
    if skill_dir:
        candidates.append(os.path.join(skill_dir, "templates", "dossier-template.md"))
    # 脚本自身所在目录的上级（仓库根）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(script_dir, "..", "templates", "dossier-template.md"))
    # 工作目录（向后兼容）
    candidates.append(os.path.join(workdir, "templates", "dossier-template.md"))
    for path in candidates:
        resolved = os.path.abspath(path)
        if os.path.isfile(resolved):
            return resolved
    return None


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------

def run_checks(workdir, overdue_days, skill_dir=None):
    today = datetime.date.today()
    problems = []  # 每条 (级别, 文字)

    contracts_dir = os.path.join(workdir, "ip-contracts")
    dossier_path = os.path.join(workdir, "ip-dossier.md")
    template_dossier = find_template_dossier(workdir, skill_dir)

    # ---- 扫契约 ----
    contract_files = []
    if os.path.isdir(contracts_dir):
        for name in sorted(os.listdir(contracts_dir)):
            if name.startswith("C-") and name.endswith(".md"):
                contract_files.append(os.path.join(contracts_dir, name))

    contracts = []
    seen_cids = set()
    for cp in contract_files:
        c = parse_contract(cp)
        if c is None:
            problems.append(("错误", "无法读取契约：%s" % os.path.basename(cp)))
            continue
        cid = c.get("contract_id")
        if cid in seen_cids:
            problems.append(("错误", "契约编号冲突：%s 存在多份契约文件" % cid))
        seen_cids.add(cid)
        contracts.append(c)

    # (a)(b)(c) 状态检查 + 状态-日期联动 + definitive 字段校验
    overdue_review = []
    suspected_unfilled = []
    bad_status = []
    status_date_violations = []
    sign_date_warnings = []
    review_days_warnings = []
    draft_review_warnings = []
    date_violations = []
    missing_fields = []
    cid_conflicts = []
    frontmatter_errors = []
    abandoned_count = 0

    for c in contracts:
        cid = c.get("contract_id") or os.path.basename(c["path"])
        status = c.get("status", "").strip()

        # 必填字段缺失
        if not status:
            missing_fields.append((cid, "status"))
        if not c.get("contract_id"):
            missing_fields.append((cid, "contract_id"))

        # frontmatter 存在但解析失败
        if "frontmatter_error" in c:
            frontmatter_errors.append((cid, c["frontmatter_error"]))

        if status and status not in VALID_STATUS:
            bad_status.append((cid, c.get("status_raw", status), c["path"]))

        # 编号冲突（文件名 vs frontmatter）
        if "contract_id_conflict" in c:
            fm_cid, file_cid = c["contract_id_conflict"]
            cid_conflicts.append((cid, fm_cid, file_cid))

        nrd_raw = c.get("next_review_date", "")
        nrd_empty = (not nrd_raw) or is_placeholder(nrd_raw)
        nrd = None if nrd_empty else parse_date(nrd_raw)

        ppd_raw = c.get("plan_publish_date", "")
        ppd_empty = (not ppd_raw) or is_placeholder(ppd_raw)
        ppd = None if ppd_empty else parse_date(ppd_raw)
        apd_raw = c.get("actual_publish_date", "")
        apd_empty = (not apd_raw) or is_placeholder(apd_raw)
        apd = None if apd_empty else parse_date(apd_raw)
        rad_raw = c.get("review_after_days", "")
        rad_empty = (not rad_raw) or is_placeholder(str(rad_raw))
        rad = None if rad_empty else parse_positive_int(rad_raw)

        # sign_date 是 definitive 字段之一，旧契约缺失时保留警告级兼容。
        sd_raw = c.get("sign_date", "")
        sd = None if not sd_raw or is_placeholder(sd_raw) else parse_date(sd_raw)
        if sd is None:
            sign_date_warnings.append((cid, "签订日期"))

        if not rad_empty and rad is None:
            date_violations.append((cid, "review_after_days 必须是正整数"))
        elif rad_empty:
            review_days_warnings.append(cid)

        if status != "已废弃":
            if ppd_empty:
                date_violations.append((cid, "预计发布日期为空"))
            elif ppd is None:
                date_violations.append((cid, "预计发布日期不是有效日期：%s" % ppd_raw))

        if not apd_empty and apd is None:
            date_violations.append((cid, "实际发布日期不是有效日期：%s" % apd_raw))
        if not nrd_empty and nrd is None:
            date_violations.append((cid, "下次复盘日不是有效日期：%s" % nrd_raw))

        if status != "已废弃":
            if sd and ppd and sd > ppd:
                date_violations.append((cid, "签订日期晚于预计发布日期"))
            if sd and apd and sd > apd:
                date_violations.append((cid, "签订日期晚于实际发布日期"))
            if apd and nrd and nrd <= apd:
                date_violations.append((cid, "下次复盘日必须晚于实际发布日期"))
            if apd and nrd and rad:
                expected_nrd = apd + datetime.timedelta(days=rad)
                if nrd != expected_nrd:
                    date_violations.append(
                        (cid, "下次复盘日应为实际发布日期 + %d 天（应为 %s）"
                         % (rad, expected_nrd.isoformat()))
                    )

        # 已废弃：终态，不纳入逾期/超期/复盘提醒计算
        if status == "已废弃":
            abandoned_count += 1
            if not nrd_empty:
                status_date_violations.append(
                    (cid, "status=已废弃 但下次复盘日未清空"))
            continue

        # (a) 过期待复盘：仅 status=待复盘 且 next_review_date 已过
        if status == "待复盘" and nrd and nrd < today:
            overdue_review.append((cid, nrd.isoformat()))

        # (b) 疑似漏回填：仅 status=待发布 且 预计发布日已过 N 天 且 实际发布日仍空
        if status == "待发布" and ppd and apd_empty:
            if (today - ppd).days > overdue_days:
                suspected_unfilled.append(
                    (cid, ppd.isoformat(), (today - ppd).days))

        # 状态-日期联动校验
        if status == "待发布":
            if not apd_empty:
                status_date_violations.append(
                    (cid, "status=待发布 但实际发布日已回填，应转为 待复盘"))
            if not nrd_empty:
                draft_review_warnings.append((cid, nrd_raw))
        elif status == "待复盘":
            if apd_empty:
                status_date_violations.append(
                    (cid, "status=待复盘 但实际发布日为空"))
            if not nrd:
                status_date_violations.append(
                    (cid, "status=待复盘 但下次复盘日为空或无效"))
        elif status == "已复盘":
            # 已复盘意味着已经发布并复盘，actual_publish_date 是发布历史，应保留。
            if apd_empty:
                status_date_violations.append(
                    (cid, "status=已复盘 但实际发布日为空（复盘应以已发布为前提）"))
            if nrd:
                status_date_violations.append(
                    (cid, "status=已复盘 但下次复盘日未清空"))

    # ---- schema_version 比对 ----
    schema_warn = None
    dossier_schema_version = ""
    dossier_text = read_text(dossier_path)
    if dossier_text is not None:
        dossier_schema_version = parse_schema_version(dossier_text)
    if template_dossier:
        tpl_text = read_text(template_dossier)
        if dossier_text is not None and tpl_text is not None:
            d_ver = dossier_schema_version
            t_ver = parse_schema_version(tpl_text)
            if d_ver and t_ver and d_ver != t_ver:
                schema_warn = (d_ver, t_ver, template_dossier)
    else:
        problems.append(("提醒", "未找到 templates/dossier-template.md，schema_version 检查跳过"))

    # ---- v1.9 建档诊断状态与完成门槛 ----
    onboarding_status = ""
    onboarding_step = ""
    onboarding_missing = []
    if dossier_text is not None and dossier_schema_version == "1.9":
        dossier_fm, dossier_fm_error = parse_frontmatter(dossier_text)
        if dossier_fm_error:
            problems.append(("错误", "dossier frontmatter 解析失败：%s" % dossier_fm_error))
        onboarding_status = dossier_fm.get("onboarding_status", "").strip()
        onboarding_step = dossier_fm.get("onboarding_step", "").strip()

        if onboarding_status not in VALID_ONBOARDING_STATUS:
            problems.append(("错误", "建档状态非法：onboarding_status=%r（合法值：in_progress / provisional / confirmed）"
                             % onboarding_status))
        if onboarding_step not in VALID_ONBOARDING_STEPS:
            problems.append(("错误", "建档断点非法：onboarding_step=%r（合法值：goal / evidence / audience / value / business / execution）"
                             % onboarding_step))

        if onboarding_status == "in_progress":
            problems.append(("提醒", "建档诊断进行中：档案尚未完成，下次从 %s 模块续访"
                             % (onboarding_step or "未记录断点")))
        elif onboarding_status in ("provisional", "confirmed"):
            onboarding_missing = onboarding_missing_fields(dossier_text)
            if onboarding_step != "execution":
                problems.append(("错误", "建档状态与断点冲突：%s 必须在六模块完成后保留 onboarding_step=execution"
                                 % onboarding_status))
            for field in onboarding_missing:
                problems.append(("错误", "建档核心字段缺失：%s 档案中“%s”未填或仍为占位值"
                                 % (onboarding_status, field)))
            if not has_onboarding_evidence_row(dossier_text):
                problems.append(("错误", "建档依据账本缺失：%s 档案至少需一条“已确认事实 / 暂定假设 / 未知”记录，且写明依据与下一步验证"
                                 % onboarding_status))
            if onboarding_status == "provisional" and not onboarding_missing:
                problems.append(("提醒", "当前是 provisional v0.1 暂定档案：可进入首批内容与契约验证，不得当作最终定位"))

    # ---- 契约索引区比对 ----
    index_mismatches = []
    if dossier_text is not None:
        dossier_index = parse_dossier_index(dossier_text)
        file_index = {}
        for c in contracts:
            cid = c.get("contract_id")
            if not cid:
                continue
            file_index[cid] = {
                "title": c.get("title", ""),
                "status": c.get("status", ""),
                "status_raw": c.get("status_raw", c.get("status", "")),
                "next_review_date": c.get("next_review_date", ""),
            }
        # 文件里有、索引表里没有。即使索引仍是空模板，也必须报告，避免
        # “存在契约但索引为空”被误判为正常。
        for cid, info in file_index.items():
            if cid not in dossier_index:
                index_mismatches.append(
                    ("缺失", cid, "契约文件存在，但 dossier 索引区无此条目"))
            else:
                di = dossier_index[cid]
                if (di["status"] or info["status"]) and di["status"] != info["status"]:
                    index_mismatches.append(
                        ("状态不符", cid,
                         "索引区=%s，契约原件=%s" % (di.get("status_raw", di["status"]),
                                                info.get("status_raw", info["status"]))))
                di_nrd = di["next_review_date"]
                fi_nrd = info["next_review_date"]
                di_nrd_normalized = "" if is_placeholder(di_nrd) else di_nrd
                fi_nrd_normalized = "" if is_placeholder(fi_nrd) else fi_nrd
                if di_nrd_normalized != fi_nrd_normalized:
                    index_mismatches.append(
                        ("复盘日不符", cid,
                         "索引区=%s，契约原件=%s"
                         % (di_nrd_normalized or "空", fi_nrd_normalized or "空")))
                # 标题一致性（宽松：忽略空白和首尾标点）
                di_title = re.sub(r"[\s，。！？、]", "", di["title"])
                fi_title = re.sub(r"[\s，。！？、]", "", info["title"])
                if (di_title or fi_title) and di_title != fi_title:
                    index_mismatches.append(
                        ("选题不符", cid,
                         "索引区=%s，契约正文=%s" % (di["title"], info["title"])))
        # 索引表里有、文件里没有（孤儿）
        for cid in dossier_index:
            if cid not in file_index:
                index_mismatches.append(
                    ("孤儿", cid, "dossier 索引区有此条目，但 ip-contracts/ 无对应文件"))

    # ---- 汇总 problem ----
    for cid, nrd in overdue_review:
        problems.append(("提醒", "过期待复盘：%s  下次复盘日 %s（已过 %d 天）"
                         % (cid, nrd, (today - parse_date(nrd)).days)))
    for cid, ppd, days in suspected_unfilled:
        problems.append(("提醒", "疑似漏回填：%s  预计发布日 %s 已过 %d 天，实际发布日仍空（可能已发未回填）"
                         % (cid, ppd, days)))
    for cid, bad, path in bad_status:
        problems.append(("错误", "状态非法值：%s  status=%r（合法值：待发布 / 待复盘 / 已复盘 / 已废弃）文件：%s"
                         % (cid, bad, os.path.basename(path))))
    for cid, field in missing_fields:
        problems.append(("错误", "字段缺失：%s  未填写 %s" % (cid, field)))
    for cid, err in frontmatter_errors:
        problems.append(("错误", "frontmatter 解析失败：%s  %s" % (cid, err)))
    for cid, fm_cid, file_cid in cid_conflicts:
        problems.append(("警告", "编号冲突：%s  frontmatter=%s，文件名=%s，以文件名为准"
                         % (cid, fm_cid, file_cid)))
    for cid, msg in status_date_violations:
        problems.append(("错误", "状态机违规：%s  %s" % (cid, msg)))
    for cid, msg in date_violations:
        problems.append(("错误", "日期字段违规：%s  %s" % (cid, msg)))
    for cid, field in sign_date_warnings:
        problems.append(("警告", "definitive 字段 %s 缺失/占位/无法解析：%s（7 个 definitive 字段：编号 / 状态 / 签订日期 / 预计发布日期 / 实际发布日期 / 发布后几天复盘 / 下次复盘日）"
                         % (field, cid)))
    for cid in review_days_warnings:
        problems.append(("警告", "definitive 字段 发布后几天复盘 缺失/占位：%s（旧契约仍可读取；下次编辑时补 review_after_days，默认 3）"
                         % cid))
    for cid, nrd_raw in draft_review_warnings:
        problems.append(("警告", "状态机违规：%s  status=待发布 但下次复盘日已填写（应为空，发布后再生成）"
                         % cid))
    if schema_warn:
        problems.append(("警告", "schema_version 不一致：ip-dossier.md=%s，模板=%s（%s）"
                         % (schema_warn[0], schema_warn[1], schema_warn[2])))
    for kind, cid, desc in index_mismatches:
        problems.append(("警告", "索引脱节[%s]：%s  %s" % (kind, cid, desc)))

    return problems, {
        "contracts": len(contracts),
        "abandoned_count": abandoned_count,
        "has_dossier": dossier_text is not None,
        "has_contracts_dir": os.path.isdir(contracts_dir),
        "template_dossier": template_dossier,
        "onboarding_status": onboarding_status,
        "onboarding_step": onboarding_step,
        "onboarding_missing": onboarding_missing,
    }


def print_report(problems, stats, workdir, overdue_days):
    print("=" * 60)
    print("ip-strategist 状态一致性校验")
    print("工作目录：%s" % os.path.abspath(workdir))
    print("逾期天数 N=%d（待发布超 N 天未回填 = 疑似漏回填）" % overdue_days)
    if stats.get("template_dossier"):
        print("模板档案：%s" % stats["template_dossier"])
    print("=" * 60)

    if not stats["has_dossier"]:
        print("\n[提示] 未找到 ip-dossier.md（schema 与索引检查跳过）。")
    if not stats["has_contracts_dir"]:
        print("\n[提示] 未找到 ip-contracts/ 目录（契约检查跳过）。")
    if stats.get("onboarding_status"):
        print("\n建档诊断：%s（当前断点：%s）"
              % (stats["onboarding_status"], stats.get("onboarding_step") or "未记录"))

    print("\n契约数量：%d 份" % stats["contracts"])
    if stats.get("abandoned_count"):
        print("已废弃：%d 份" % stats["abandoned_count"])

    if not problems:
        print("\n[通过] 未发现一致性问题，一切对齐。")
        return

    # 按级别分组
    order = {"错误": 0, "警告": 1, "提醒": 2}
    problems.sort(key=lambda p: order.get(p[0], 9))

    print("\n发现 %d 条问题：" % len(problems))
    print("-" * 60)
    for level, msg in problems:
        print("[%s] %s" % (level, msg))
    print("-" * 60)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="ip-strategist 状态一致性校验工具（零依赖）。",
        epilog="检查契约状态机、档案 schema_version、契约索引区一致性；可安全重建索引。\n"
               "退出码：0=正常/仅提醒，1=有警告，2=有错误，3=参数错误。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("workdir", nargs="?", default=".",
                        help="工作目录（含 ip-dossier.md 与 ip-contracts/），默认当前目录")
    parser.add_argument("overdue_days", nargs="?", type=int, default=3,
                        help="待发布超期阈值 N（天），默认 3（与 SKILL.md 启动协议一致）")
    parser.add_argument("--skill-dir", dest="skill_dir", default=None,
                        help="skill 安装目录（含 templates/dossier-template.md），默认自动探测")
    parser.add_argument("--sync-index", action="store_true",
                        help="校验无错误后，从 ip-contracts/ 原子重建 dossier 契约索引（先备份为 .bak）")
    args = parser.parse_args(argv)

    workdir = args.workdir
    if not os.path.isdir(workdir):
        print("[错误] 工作目录不存在：%s" % workdir, file=sys.stderr)
        return 3

    problems, stats = run_checks(workdir, args.overdue_days, args.skill_dir)
    if args.sync_index:
        if any(p[0] == "错误" for p in problems):
            print("[错误] 存在错误级问题，未执行索引同步。", file=sys.stderr)
        else:
            try:
                count = sync_dossier_index(workdir)
            except (OSError, ValueError) as exc:
                print("[错误] 索引同步失败：%s" % exc, file=sys.stderr)
                return 3
            print("[同步] 已从 %d 份契约重建 dossier 索引；发生修改时已备份为 ip-dossier.md.bak。"
                  % count)
            problems, stats = run_checks(workdir, args.overdue_days, args.skill_dir)
    print_report(problems, stats, workdir, args.overdue_days)

    if any(p[0] == "错误" for p in problems):
        return 2
    if any(p[0] == "警告" for p in problems):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
