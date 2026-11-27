#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chapters/ の原稿から、原稿閲覧ページ（1 枚の HTML）を組み立てる。

外部ライブラリを使わない。macOS 標準の python3 でそのまま動く。

    python3 tools/build_viewer.py                    # 修正箇所の指定なし
    python3 tools/build_viewer.py --focus 3:31,161   # 第3章の31行・161行を「直近の修正」にする

出力：
    dist/viewer/index.html

設定（novel.config.json）：
    title              ページの見出しに出す作品名
    viewer.slug / url  公開先の Artifact。空なら、初回の公開で新しく作る（下の手順）
    viewer.label       章題の横に出す短い札（例：「初稿」「改稿版」）。空なら出さない
    viewer.storage_key ブラウザーに読みかけの位置を覚えるときの名前。空なら clone したフォルダーの名前
                       ＋「-viewer」を使う。セッションと Mac でずれないよう、初回の公開で設定へ書き込む
    viewer.accent      アクセントの色（#rrggbb）。空なら既定の青。暗い表示用の色は自動で作る

ページの仕様（tools/viewer_template.html が持つ）：
    - 縦書き・横書きの切り替え、文字の大きさ、行番号の表示（行番号は元ファイルの行番号）
    - 「行へ移動」の入力欄。#ch3-L17 のような URL でも行を開ける
    - --focus で指定した章・行を、新しい版を最初に開いたときに表示し、色で示す
      （2 回目以降は、そのブラウザーで前回読んでいた章と行に戻る）
    - 場面の区切り（`---` だけの行）は「◇　◇　◇」で表示する

公開の手順（Claude が行う）：
    1. 本文を修正して commit・push したあと、このスクリプトを --focus 付きで実行する
       （FOCUS の id は HEAD の短いハッシュと --focus の値から作るので、push 後に実行する）
    2. novel.config.json の viewer.slug が空なら、Artifact の publish_files を slug なしで呼んで新しく作る。
       title は「〈作品名〉 原稿閲覧」（このスクリプトが最後に表示する）、icon は book とする。
       返ってきた slug と URL、このスクリプトが表示した storage_key を novel.config.json に書き戻し、commit・push する
    3. slug があれば、get_artifact で現在の version を確かめ、publish_files に slug と base_version を渡して
       dist/viewer/index.html を index.html として公開し直す

ページの見た目や動きを変えるときは tools/viewer_template.html を編集する。
CH（章データ）・FOCUS（直近の修正）・CONF（設定）と見出しの文字は、このスクリプトが差し込む。
"""

import argparse
import html as htmllib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import count_chars  # noqa: E402
import novelconf  # noqa: E402

ROOT = novelconf.ROOT
CHAPTERS = ROOT / "chapters"
TEMPLATE = Path(__file__).resolve().parent / "viewer_template.html"
OUT = ROOT / "dist" / "viewer" / "index.html"


def load_chapters():
    chapters = []
    for path in sorted(CHAPTERS.glob("[0-9][0-9]_*.md")):
        lines = path.read_text(encoding="utf-8").split("\n")
        chapters.append({
            "n": int(path.name[:2]),
            "title": lines[0].lstrip("# ").strip(),
            "chars": count_chars.count(path),
            # 1 行目（章見出し）と空行を除き、元ファイルの行番号を付ける
            "lines": [[k + 1, l] for k, l in enumerate(lines) if k > 0 and l.strip() != ""],
        })
    if not chapters:
        sys.exit("chapters/ に章ファイル（NN_章題.md）がありません")
    return chapters


def parse_focus(spec, chapters):
    if not spec:
        return None
    m = re.fullmatch(r"(\d+):(\d+(?:,\d+)*)", spec)
    if not m:
        sys.exit(f"--focus の形式が違います（例：3:31,161）：{spec}")
    n, lines = int(m.group(1)), [int(x) for x in m.group(2).split(",")]
    ch = next((c for c in chapters if c["n"] == n), None)
    if ch is None:
        sys.exit(f"第{n}章のファイルがありません")
    known = {k for k, _ in ch["lines"]}
    missing = [x for x in lines if x not in known]
    if missing:
        sys.exit(f"第{n}章に本文のない行が指定されています（空行・範囲外）：{missing}")
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() or "local"
    return {"id": f"{head}-{spec}", "n": n, "lines": lines}


DEFAULT_ACCENT = "#2f5d7c"


def mix(hex1, hex2, t):
    """2 色を t（0〜1、hex2 の割合）で混ぜる。"""
    a = [int(hex1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def accent_colors(value):
    accent = value or DEFAULT_ACCENT
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        sys.exit(f"viewer.accent は #rrggbb の形で書いてください：{accent}")
    accent = accent.lower()
    return {
        "{{ACCENT}}": accent,
        "{{ACCENT_WASH}}": mix(accent, "#ffffff", 0.88),
        "{{ACCENT_DARK}}": mix(accent, "#ffffff", 0.45),
        "{{ACCENT_WASH_DARK}}": mix(accent, "#15181a", 0.78),
    }


def main():
    ap = argparse.ArgumentParser(description="原稿閲覧ページを組み立てる")
    ap.add_argument("--focus", help="直近の修正箇所（章:行,行…）例 3:31,161")
    ap.add_argument("-o", "--output", type=Path, default=OUT, help="出力先（既定 dist/viewer/index.html）")
    args = ap.parse_args()

    conf = novelconf.load()
    title = novelconf.title_or_placeholder(conf)
    viewer = conf["viewer"]
    client = {
        "storageKey": viewer.get("storage_key") or (ROOT.name + "-viewer"),
        "label": viewer.get("label") or "",
    }

    chapters = load_chapters()
    focus = parse_focus(args.focus, chapters)
    html = TEMPLATE.read_text(encoding="utf-8")
    for marker, value in (("/*CHAPTERS*/[]", json.dumps(chapters, ensure_ascii=False)),
                          ("/*FOCUS*/null", json.dumps(focus, ensure_ascii=False)),
                          ("/*CONF*/{}", json.dumps(client, ensure_ascii=False)),
                          ("{{VIEWER_TITLE}}", htmllib.escape(f"{title} 原稿閲覧")),
                          ("{{BOOK_TITLE}}", htmllib.escape(title))):
        if html.count(marker) != 1:
            sys.exit(f"テンプレートに差し込み位置 {marker} が 1 つだけ必要です")
        html = html.replace(marker, value)
    for marker, value in accent_colors(viewer.get("accent", "")).items():
        if marker not in html:
            sys.exit(f"テンプレートに差し込み位置 {marker} がありません")
        html = html.replace(marker, value)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    where = viewer.get("url") or "（未公開。初回の公開で Artifact を作る）"
    print(f"{args.output}（{len(chapters)}章、FOCUS={focus['id'] if focus else 'なし'}）")
    print(f"公開先：{where}")
    print(f"Artifact の title：{title} 原稿閲覧")
    if not viewer.get("storage_key"):
        print(f"storage_key（設定に書き込む値）：{client['storageKey']}")


if __name__ == "__main__":
    main()
