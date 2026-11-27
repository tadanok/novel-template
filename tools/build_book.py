#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chapters/ の原稿から、私家版の EPUB と HTML を組み立てる。

外部ライブラリを使わない。macOS 標準の python3 でそのまま動く。

    python3 tools/build_book.py

出力（〈作品名〉は novel.config.json の title）：
    dist/〈作品名〉.epub   スマホ・Kindle・Apple Books で読む用
    dist/〈作品名〉.html   ブラウザで開き、印刷から PDF にする用

設定（novel.config.json）：
    title / author   表紙ページと EPUB の書誌情報
    episode_label    見出しの「第N話」の「話」（「章」などに変えられる）
    notice           冒頭の注意書き
    cover_image      表紙画像（PNG）のパス。無ければ表紙なしで組む
"""

import html
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import count_chars  # noqa: E402
import novelconf  # noqa: E402

ROOT = novelconf.ROOT
CHAPTERS = ROOT / "chapters"
DIST = ROOT / "dist"

CONF = novelconf.load()
TITLE = novelconf.title_or_placeholder(CONF)
AUTHOR = CONF["author"]
NOTICE = CONF["notice"]
LABEL = CONF["episode_label"] or "話"
COVER = ROOT / CONF["cover_image"] if CONF["cover_image"] else None

CSS = """
html { font-size: 16px; }
body {
  font-size: 1.08rem;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
  line-height: 2;
  margin: 1.2em;
  color: #1a1a1a;
  background: #fdfdfb;
}
h1.book-title { font-size: 1.7em; line-height: 1.5; margin: 3em 0 0.4em; text-align: center; }
p.book-author { text-align: center; color: #666; margin-bottom: 4em; }
p.notice {
  font-size: 0.85em; color: #8a6d3b; background: #fcf8e3;
  border: 1px solid #f0e0b0; padding: 0.8em 1em; margin: 2em 0; line-height: 1.7;
}
h2.chapter { font-size: 1.25em; margin: 3.5em 0 1.8em; padding-bottom: 0.4em;
  border-bottom: 1px solid #ddd; }
p { text-indent: 1em; margin: 0 0 0.2em; }
p.dialogue, p.noindent { text-indent: 0; }
hr.scene { border: 0; margin: 2em 0; text-align: center; }
hr.scene:after { content: "＊"; color: #999; }
nav ol { line-height: 2; }
@media print {
  body { background: #fff; margin: 0; }
  h2.chapter { page-break-before: always; }
  p.notice { break-inside: avoid; }
}
"""


def esc(s):
    return html.escape(s, quote=False)


def md_to_xhtml(text):
    """散文の Markdown を最小限の XHTML に変換する。"""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        if re.fullmatch(r"(---+|\*\*\*+|＊|\*)", block):
            out.append('<hr class="scene" />')
            continue
        if block.startswith("#"):
            continue  # 章題は別途扱う
        lines = [esc(l.strip()) for l in block.split("\n") if l.strip()]
        for line in lines:
            line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            cls = "dialogue" if line[:1] in "「『（(" else ""
            attr = f' class="{cls}"' if cls else ""
            out.append(f"<p{attr}>{line}</p>")
    return "\n".join(out)


def load_chapters():
    files = sorted(p for p in CHAPTERS.glob("*.md") if re.match(r"^\d{2}_", p.name))
    if not files:
        sys.exit("chapters/ に NN_章題.md 形式のファイルがありません。")
    chapters = []
    for i, path in enumerate(files, start=1):
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", raw, flags=re.M)
        heading = m.group(1).strip() if m else path.stem.split("_", 1)[-1]
        # 「第一章　章題」のような章番号の接頭辞を落とす（話数は別に付けるため）
        heading = re.sub(r"^第[0-9一二三四五六七八九十百]+[章話][\s\u3000:：]*", "", heading).strip()
        chapters.append({
            "no": i,
            "file": path.name,
            "title": heading,
            "body": md_to_xhtml(raw),
            "chars": count_chars.count(path),  # tools/count_chars.py と同じ数え方
        })
    return chapters


def build_html(chapters):
    parts = [
        "<!DOCTYPE html>",
        '<html lang="ja"><head><meta charset="utf-8" />',
        f"<title>{esc(TITLE)}</title>",
        f"<style>{CSS}</style></head><body>",
        f'<h1 class="book-title">{esc(TITLE)}</h1>',
        f'<p class="book-author">{esc(AUTHOR)}</p>',
        f'<p class="notice">{esc(NOTICE)}</p>',
    ]
    for c in chapters:
        parts.append(f'<h2 class="chapter">第{c["no"]}{LABEL}　{esc(c["title"])}</h2>')
        parts.append(c["body"])
    parts.append("</body></html>")
    return "\n".join(parts)


def xhtml_page(title, body):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">\n'
        f"<head><meta charset=\"utf-8\" /><title>{esc(title)}</title>"
        '<link rel="stylesheet" type="text/css" href="style.css" /></head>\n'
        f"<body>\n{body}\n</body></html>"
    )


def build_epub(chapters, path):
    uid = "urn:uuid:" + str(uuid.uuid4())
    has_cover = bool(COVER and COVER.exists())

    items, spine, nav_items = [], [], []

    title_body = (
        f'<h1 class="book-title">{esc(TITLE)}</h1>'
        f'<p class="book-author">{esc(AUTHOR)}</p>'
        f'<p class="notice">{esc(NOTICE)}</p>'
    )
    pages = {"title.xhtml": xhtml_page(TITLE, title_body)}
    items.append('<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>')
    spine.append('<itemref idref="title"/>')

    for c in chapters:
        name = f"ch{c['no']:02d}.xhtml"
        head = f'<h2 class="chapter">第{c["no"]}{LABEL}　{esc(c["title"])}</h2>'
        pages[name] = xhtml_page(c["title"], head + "\n" + c["body"])
        items.append(f'<item id="ch{c["no"]:02d}" href="{name}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="ch{c["no"]:02d}"/>')
        nav_items.append(f'<li><a href="{name}">第{c["no"]}{LABEL}　{esc(c["title"])}</a></li>')

    nav = xhtml_page(
        "目次",
        '<nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">'
        "<h2>目次</h2><ol>" + "".join(nav_items) + "</ol></nav>",
    )

    cover_meta = ""
    if has_cover:
        items.append('<item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>')
        cover_meta = '<meta name="cover" content="cover-image"/>'

    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{uid}</dc:identifier>
    <dc:title>{esc(TITLE)}</dc:title>
    <dc:creator>{esc(AUTHOR)}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}</meta>
    {cover_meta}
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
    {chr(10).join("    " + i for i in items)}
  </manifest>
  <spine>
    {chr(10).join("    " + s for s in spine)}
  </spine>
</package>"""

    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, zipfile.ZIP_DEFLATED)
        for name, content in pages.items():
            z.writestr("OEBPS/" + name, content, zipfile.ZIP_DEFLATED)
        if has_cover:
            z.write(COVER, "OEBPS/cover.png")


def main():
    chapters = load_chapters()
    DIST.mkdir(exist_ok=True)

    html_path = DIST / f"{novelconf.safe_filename(TITLE)}.html"
    html_path.write_text(build_html(chapters), encoding="utf-8")

    epub_path = DIST / f"{novelconf.safe_filename(TITLE)}.epub"
    build_epub(chapters, epub_path)

    total = sum(c["chars"] for c in chapters)
    print(f"収録: {len(chapters)}章 / 合計 約{total:,}字")
    for c in chapters:
        print(f"  第{c['no']}{LABEL} {c['title']}  {c['chars']:,}字")
    print()
    print(f"EPUB: {epub_path}  ({epub_path.stat().st_size:,} バイト)")
    print(f"HTML: {html_path}  ({html_path.stat().st_size:,} バイト)")
    if not (COVER and COVER.exists()):
        print(f"（表紙画像がまだありません。{CONF['cover_image'] or 'novel.config.json の cover_image'} を置くと表紙が付きます）")


if __name__ == "__main__":
    main()
