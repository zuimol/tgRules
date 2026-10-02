#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""屏蔽词收集 + 分类正则生成器。直接运行（不带参数）就按下面的配置生成正则。

    python blocklist.py                 # 按配置生成（当前：哔哩哔哩写法 + 复制）
    python blocklist.py add 引流 "加微信" -t "到处引流"
    python blocklist.py list
    python blocklist.py gen             # 同直接运行，可用 -f/-o 临时改
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ============================== 配置 ==============================
# 生成的写法：
#   bilibili -> /(词1|词2)/     哔哩哔哩站内「弹幕 / 评论屏蔽词」
#   generic  -> (?i)(词1|词2)   Python / PCRE / Java，安卓第三方 TG 客户端
#   java / pcre 与 generic 相同；js -> (词1|词2)（忽略大小写靠调用方的 i 标志）
FLAVOR = "bilibili"

# 生成后是否自动复制到剪贴板
COPY = True

# 非空则同时把正则写入该文件（如 "rules.txt"），留空表示不写文件
OUTPUT = ""

# 只记录、不参与生成正则的分类（词照常攒着，gen 默认跳过）
# 内容可以是现成的整条正则；显式写 gen 分类名 时原样输出，不转义、不合并
RECORD_ONLY = {"互动刷屏"}

# 数据文件位置，改成绝对路径也可以（如 r"D:\my\rules.json"）
DATA = Path(__file__).resolve().parent / "data" / "blocked_words.json"
# ==================================================================

META = set("\\^$.|?*+()[]{}")
# 每个分类生成一条正则，目标不同只是外壳不同
FLAVORS = {
    "generic": "(?i)({})",
    "java": "(?i)({})",
    "pcre": "(?i)({})",
    "js": "({})",
    "bilibili": "/({})/",
}


def load():
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}


def save(cats):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(cats, ensure_ascii=False, indent=2), encoding="utf-8")


def escape(word):
    return "".join("\\" + c if c in META else c for c in word)


def tag_of(cat):
    return "（仅记录）" if cat in RECORD_ONLY else ""


def regex_of(words, flavor="generic"):
    # 去重 + 长词排在前面（短词先来会先把长词的一部分吃掉）；同级保持录入顺序
    alts = sorted(dict.fromkeys(escape(w) for w in words), key=len, reverse=True)
    return FLAVORS[flavor].format("|".join(alts))


def copy(text):
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Console]::InputEncoding=[Text.Encoding]::UTF8;Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=text, text=True, encoding="utf-8", check=False,
    )


def cmd_add(a, cats):
    # 参数写全就是一条命令批量加；只写一半或全不写才接着问
    cat = a.category or input("分类：").strip()
    if not a.word:
        a.word = input("屏蔽词：").strip()
        a.thought = a.thought or input("想法（可留空）：").strip()
    thought = a.thought or ""
    entries = cats.setdefault(cat, [])
    for entry in entries:
        if entry["word"] == a.word:
            entry["thought"] = thought or entry["thought"]
            break
    else:
        entries.append({"word": a.word, "thought": thought,
                        "added_at": datetime.now().isoformat(timespec="seconds")})
    save(cats)
    print(f"已记录：{cat} → {a.word}{tag_of(cat)}")


def cmd_list(a, cats):
    for cat, entries in cats.items():
        for entry in entries:
            print(f"{cat}{tag_of(cat)} | {entry['word']} | {entry['thought']} | {entry['added_at']}")


def cmd_cats(a, cats):
    for cat, entries in cats.items():
        print(f"{cat}{tag_of(cat)}：{len(entries)} 个词")


def cmd_rm(a, cats):
    cats[a.category][:] = [e for e in cats[a.category] if e["word"] != a.word]
    if not cats[a.category]:
        del cats[a.category]
    save(cats)
    print(f"已删除：{a.word}")


def cmd_thought(a, cats):
    for entry in cats[a.category]:
        if entry["word"] == a.word:
            entry["thought"] = a.thought
            save(cats)
            return print(f"已更新想法：{a.word}")
    print(f"没找到：{a.word}")


def cmd_gen(a, cats):
    if a.categories:
        names = a.categories
    else:
        names = [n for n in cats if n not in RECORD_ONLY]
        skipped = [n for n in cats if n in RECORD_ONLY and cats[n]]
        if skipped:
            print(f"（跳过仅记录分类：{'、'.join(skipped)}）", file=sys.stderr)
    lines = []
    for n in names:
        words = [e["word"] for e in (cats.get(n) or [])]
        if not words:
            continue
        lines.append("\n".join(words) if n in RECORD_ONLY else regex_of(words, a.flavor or FLAVOR))
    text = "\n".join(lines)
    print(text)
    out = a.output or OUTPUT
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
        print(f"（已写入 {out}）")
    if a.copy or COPY:
        copy(text)
        print("（已复制到剪贴板）")


def main():
    p = argparse.ArgumentParser(description="屏蔽词收集 + 分类正则生成器（不带参数 = 按文件顶部配置生成）")
    sub = p.add_subparsers(dest="cmd")

    q = sub.add_parser("add", help="记录屏蔽词和想法（不写参数就一路问答）")
    q.add_argument("category", nargs="?")
    q.add_argument("word", nargs="?")
    q.add_argument("-t", "--thought")

    sub.add_parser("list", help="全部屏蔽词和想法，一行一条")
    sub.add_parser("cats", help="各分类的词数")

    q = sub.add_parser("rm", help="删除屏蔽词")
    q.add_argument("category")
    q.add_argument("word")

    q = sub.add_parser("thought", help="改某个词的想法")
    q.add_argument("category")
    q.add_argument("word")
    q.add_argument("thought")

    q = sub.add_parser("gen", help="每个分类生成一条正则并打印（不带参数直接运行即走这条）")
    q.add_argument("categories", nargs="*", help="只生成这些分类（省略则全部）")
    q.add_argument("-f", "--flavor", choices=FLAVORS, help=f"目标写法，默认走文件顶部配置（当前 {FLAVOR}）")
    q.add_argument("-o", "--output", help="同时写入文件")
    q.add_argument("--copy", action="store_true", help="同时复制到剪贴板")

    a = p.parse_args()
    if not a.cmd:  # 不带参数直接运行 = 按配置生成
        a = p.parse_args(["gen"])
    {"add": cmd_add, "list": cmd_list, "cats": cmd_cats,
     "rm": cmd_rm, "thought": cmd_thought, "gen": cmd_gen}[a.cmd](a, load())


if __name__ == "__main__":
    main()
