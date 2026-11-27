# -*- coding: utf-8 -*-
"""novel.config.json を読む小さな補助モジュール（tools/ のスクリプトが共通で使う）。

外部ライブラリを使わない。macOS 標準の python3（3.9 以降）で動く。
各項目の意味は docs/operations.md の「設定ファイル」を参照。
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "novel.config.json"

DEFAULTS = {
    "title": "",
    "author": "",
    "episode_label": "話",
    "notice": "これは公開前の草稿です。転載・再配布はご遠慮ください。",
    "cover_image": "publish/note/assets/cover-base.png",
    "viewer": {"slug": "", "url": "", "label": "", "storage_key": "", "accent": ""},
    "note": {},
}


def load():
    if not CONFIG.exists():
        sys.exit("novel.config.json がありません。リポジトリの直下に置いてください。")
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"novel.config.json の書式が正しくありません：{e}")
    if not isinstance(data, dict):
        sys.exit("novel.config.json は { } で囲んだ形（オブジェクト）にしてください。")
    conf = dict(DEFAULTS)
    for key, value in data.items():
        if value is None:
            continue  # null は既定値のまま
        if key in DEFAULTS and not isinstance(value, type(DEFAULTS[key])):
            sys.exit(f"novel.config.json の {key} の値の種類が違います（期待：{type(DEFAULTS[key]).__name__}）")
        conf[key] = value
    for key in ("viewer", "note"):
        merged = dict(DEFAULTS[key])
        merged.update({k: v for k, v in (data.get(key) or {}).items() if v is not None})
        conf[key] = merged
    return conf


def safe_filename(name):
    """ファイル名に使えない文字を全角の「＿」に置き換える。"""
    return re.sub(r'[\\/:*?"<>|]', "＿", name).strip() or "（題名未定）"


def title_or_placeholder(conf):
    """タイトルが未設定なら、仮の表示名を返す。"""
    return conf["title"].strip() or "（題名未定）"
