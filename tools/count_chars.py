#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原稿の字数を数える。

外部ライブラリを使わない。macOS 標準の python3 でそのまま動く。

    python3 tools/count_chars.py chapters/03_*.md
    python3 tools/count_chars.py chapters/03_*.md --target 8000
    python3 tools/count_chars.py chapters/03_*.md --scenes   # 場面ごとの字数も出す
    python3 tools/count_chars.py                      # chapters/ の全章と合計

数え方：
    ファイル全体から半角スペース・タブ・改行だけを除いた文字数（全角スペースは数える）。
    `tr -d ' \\n\\r\\t' | wc -m` と同じ定義だが、ロケールに左右されない。
    （`wc -m` はロケールによってバイト数を返すことがあり、字数が約 3 倍に見える）

--target を付けると、目安字数に対する割合を示す。
8 割未満なら「加筆が必要」、1.3 倍以上なら「冗長の確認」を表示する。

--scenes を付けると、`---` だけの行で区切った場面ごとの字数を出す。
1 行目の章見出しと `---` の行はどの場面にも数えないので、場面の合計はファイル全体の字数より少し少ない。
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOVE = {" ", "\t", "\n", "\r"}


def count(path):
    text = path.read_text(encoding="utf-8")
    return sum(1 for ch in text if ch not in REMOVE)


def scenes(path):
    """`---` だけの行で区切った場面ごとの字数（1 行目の見出しと区切りの行は除く）。"""
    lines = path.read_text(encoding="utf-8").split("\n")[1:]
    counts, cur = [], 0
    for line in lines:
        if line.strip() == "---":
            counts.append(cur)
            cur = 0
        else:
            cur += sum(1 for ch in line if ch not in REMOVE)
    counts.append(cur)
    return counts


def main():
    ap = argparse.ArgumentParser(description="原稿の字数を数える")
    ap.add_argument("files", nargs="*", type=Path, help="数えるファイル（省略時は chapters/ の全章）")
    ap.add_argument("--target", type=int, help="目安字数（1 ファイルを数えるときに使う）")
    ap.add_argument("--scenes", action="store_true", help="場面ごとの字数も出す")
    args = ap.parse_args()

    files = args.files or sorted((ROOT / "chapters").glob("[0-9][0-9]_*.md"))
    if not files:
        sys.exit("数えるファイルがありません")

    total = 0
    for path in files:
        if not path.exists():
            sys.exit(f"ファイルがありません：{path}")
        n = count(path)
        total += n
        line = f"{n:,}字  {path}"
        if args.target:
            ratio = n / args.target
            line += f"  （目安 {args.target:,}字の {ratio:.0%}）"
            if ratio < 0.8:
                line += "  → 8 割未満：加筆が必要"
            elif ratio >= 1.3:
                line += "  → 1.3 倍以上：冗長な説明がないか確認"
        print(line)
        if args.scenes:
            for k, c in enumerate(scenes(path), 1):
                print(f"    場面 {k}：{c:,}字")
    if len(files) > 1:
        print(f"合計 {total:,}字（{len(files)}ファイル）")


if __name__ == "__main__":
    main()
