#!/usr/bin/env python3
"""Check authorization docs stay generic and the v2 original stays verbatim."""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "references" / "job_search_rules_v2_20261121.md"
SKILL = ROOT / "SKILL.md"
README = ROOT / "README.md"
EXAMPLES = ROOT / "references" / "authorization-mode-examples.md"

ORIGINAL_SHA256 = "2bebc8dd02639c3673ec759f8972835bbe06df8bb2e4b39f42e498db45feddc2"

GENERIC_FILES = (SKILL, README, EXAMPLES)
PERSONAL_TOKENS = (
    "4500",
    "佛山",
    "广州",
    "深圳",
    "肇庆",
    "顺德",
    "番禺",
    "白云",
    "广交会",
    "全屋定制",
    "11:45",
    "2026-11-23",
    "resume_fact_ledger",
    "/home/",
    "/workspace",
    "/opt/",
    "/Users/",
)

EXAMPLE_HEADINGS = (
    "默认复核模式",
    "显式常设授权",
    "招呼不算投递",
    "约面试例外",
    "撤销授权",
    "未知问题跳过",
    "回执不明",
    "黑名单与已拒绝",
    "强制门",
    "对话授权不覆盖监听",
    "薪资门槛取消",
    "常规 HR 回复",
)

SKILL_NEEDLES = (
    "复核（默认）",
    "自主投递",
    "精确常设发送授权",
    "已保存指令",
    "简历申请已经提交",
    "约面试",
    "未知不能当成已合格",
    "明确取消",
    "定时任务和监听任务",
    "跳过这一条",
    "不能用来绕过",
)

errors = []


def fail(message):
    errors.append(message)


def extract_original(text):
    start = text.index("【BOSS直聘分层投递规则 v2（含销售岗）】")
    end = text.index("\n---\n\n## 二、实施说明")
    return text[start:end].strip("\n")


def main():
    rules = RULES.read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    examples = EXAMPLES.read_text(encoding="utf-8")

    original = extract_original(rules)
    digest = hashlib.sha256(original.encode()).hexdigest()
    if digest != ORIGINAL_SHA256:
        fail(f"v2 original section hash changed: {digest}")

    heads = re.findall(r"^(一|二|三|四|五|六|七|八)、", original, re.M)
    if heads != ["一", "二", "三", "四", "五", "六", "七", "八"]:
        fail(f"v2 section headings changed: {heads}")

    for needle in (
        "A档（≥75分）：当天投，个性化打招呼",
        "B档（55-74分）：标准话术投",
        "C档（<55分）：不投",
        "须当轮明确批准后才能操作",
        "≥ 4500 元",
        "## 三、发送授权与通用技能",
        "固定底薪门槛可以在当前用户自己的有效范围里明确取消",
    ):
        if needle not in rules:
            fail(f"rules file missing: {needle}")

    for path in GENERIC_FILES:
        text = path.read_text(encoding="utf-8")
        for token in PERSONAL_TOKENS:
            if token in text:
                fail(f"{path.relative_to(ROOT)} contains personal token {token!r}")

    for needle in SKILL_NEEDLES:
        if needle not in skill:
            fail(f"SKILL.md missing: {needle}")

    for heading in EXAMPLE_HEADINGS:
        if f"## {heading}" not in examples:
            fail(f"examples missing heading: {heading}")

    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in (SKILL, README, RULES, EXAMPLES):
        text = path.read_text(encoding="utf-8")
        for url in link_re.findall(text):
            if url.startswith(("http://", "https://", "mailto:")):
                fail(f"unexpected remote link in {path.name}: {url}")
                continue
            target = (path.parent / url).resolve()
            if not target.is_file():
                fail(f"broken link in {path.relative_to(ROOT)}: {url}")

    if errors:
        print("FAILED")
        for item in errors:
            print(f"- {item}")
        return 1

    print("OK")
    print(f"original_sha256={digest}")
    print("checked=SKILL.md, README.md, authorization-mode-examples.md, job_search_rules_v2_20261121.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
