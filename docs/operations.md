# 運用

作業する環境、セッションの分け方、ブランチ、コミット、設定ファイル、公開までの段取りをまとめる。
外部サービス（GitHub、note、Claude）の画面や設定の名前は 2026 年 11 月時点のもの。変わっていたら、ここを直す。

## セッションの分け方

- 1 つのセッションで 1 章だけを書く。設定と経過はすべてファイルに残るので、次の章は新しいセッションで始める。
- 原稿チェック（行番号での指摘）は、執筆とは別のセッションでもよい。直した箇所はその都度 push し、閲覧ページを公開し直す。
- 書いた本人のセッションは、自分の書いた章の矛盾を見落としやすい。点検は `continuity-checker` エージェント（別の文脈）に任せる。
- 依頼文のひな形は [docs/prompts/chapter-session.md](prompts/chapter-session.md) にある。

### 作業する環境：Claude のデスクトップ アプリ（ふだんの使い方）

- 新しいセッションの最初に、リポジトリをセッションに接続する。依頼文の 1 行目に「GitHub の <GitHub のユーザー名>/<リポジトリ名>（ブランチ <名前>）を書き込みで接続してください」と書く。
  Claude はリポジトリを clone して作業し、push する。`.claude/` のスキル・エージェント・文体ルールはそのまま使われる。
- 書き込みでの接続が一度拒否されることがある。そのときは読み取りで接続して先に正典を読み、push の前に書き込みで接続し直す。
- セッションの始めに、スキル（`/write-chapter` など）が読み込まれているかを確かめる。依頼文のスキルが見つからないと返されたら、作業に入る前にスキルの一覧を確かめさせ、読み込まれていなければリポジトリの接続からやり直す。
- 原稿の閲覧ページ（Artifact）は、アプリのサイドパネルで開ける。
- note への投稿（`/note-publish`）は、アプリの内蔵ブラウザーで行う。内蔵ブラウザーは、そのパソコンでアプリが開いていてオンラインのときだけ使える。
  note へのサインインは内蔵ブラウザーに残るので、最初の 1 回だけユーザーがサインインする。
- 同じセッションは、ウェブやスマートフォンの Claude からも続けられる。ただし、内蔵ブラウザーを使う作業は、デスクトップ アプリが開いている間に行う。

### Mac で直接作業するとき（補足）

手元のファイルで直接作業したいときは、リポジトリを clone し、VS Code の Claude Code から同じスキルを使える。`.claude/` の設定はそのまま読み込まれる。

## ブランチ

```mermaid
gitGraph
  commit id: "雛形から作成"
  commit id: "正典の初期化"
  commit id: "第1章"
  commit id: "第2章 …"
  branch revision/<版名>
  commit id: "改稿の設計"
  commit id: "第1章 改稿"
  commit id: "… 全章改稿"
  checkout main
  merge revision/<版名> id: "公開がすべて終わってから"
```

- 初稿は章ごとに `main` へ入れる。
- 構成改稿は `revision/<版名>` ブランチで行う（`/start-revision` が作る）。
- 改稿ブランチを `main` に取り込む時期は、作品ごとに決めて `plot/outline.md` の「分量の方針」の下か `plot/open_questions.md` に書く。
  公開中の作品なら、公開がすべて終わってから取り込むと、公開済みの本文と `main` が食い違わない。

## コミット

- 1 つのコミットに、本文の修正と、それに伴う記録（`log/continuity.md`・正典・`plot/outline.md` の字数）の修正をまとめる。
- メッセージの末尾に、作業した環境を 1 行書く（`Agent: Claude desktop` か `Agent: Claude Code (VS Code)`）。どのエージェントで書いたかを残しておかないと、あとから作業の経過をたどれなくなるため。
- メッセージは英語でも日本語でもよい。何を、なぜ直したかが分かるように書く（例：`Fix action order in chapter 3 (lines 41-45)`）。
- 本文を直したら、push のあとで閲覧ページを公開し直す（`--focus` に直した行を渡す）。

### Mac で直接作業するときの同期

- デスクトップ アプリのセッションは、GitHub から clone して作業し、push する。Mac で作業する前には `git pull` する。
- Mac で作業したら、次のセッションを始める前に push しておく。push していない変更は、デスクトップ アプリのセッションから見えない。
- 両方で同じブランチを同時に編集しない。

## GitHub の権限

- セッションからの push には、Claude の GitHub App がそのリポジトリにアクセスできる必要がある。
  GitHub の **Settings** › **Applications** › Claude の **Configure** で、**All repositories** か、**Only select repositories** に新しいリポジトリが入っていることを確かめる。
- push が 403 エラーになったら、まずここを確かめる。別のセッションを削除したあとに、それまで使えていた権限が外れた例がある。

## 設定ファイル（novel.config.json）

JSON はコメントを書けないので、各項目の意味をここに書く。

| 項目 | 意味 | 使う場所 |
| :-- | :-- | :-- |
| `title` | 作品名（仮題でよい）。空のあいだは「（題名未定）」と表示する | 閲覧ページ、私家版、note の記事タイトル |
| `author` | 著者名（ペンネーム）。雛形では空。`/start-novel` が尋ねて書く（`/build-book` も、空なら尋ねる） | 私家版の書誌情報 |
| `episode_label` | 「第N話」の「話」。「章」などに変えられる | 私家版、note の記事タイトル |
| `notice` | 私家版の冒頭に入れる注意書き | 私家版 |
| `cover_image` | 表紙・見出し画像の背景（PNG）のパス | 私家版、note の見出し画像 |
| `viewer.slug` / `viewer.url` | 原稿閲覧ページの Artifact。空なら初回の公開で作り、Claude が書き戻す | 閲覧ページ |
| `viewer.label` | 章題の横に出す短い札（例：「初稿」「改稿版」）。空なら出さない | 閲覧ページ |
| `viewer.storage_key` | ブラウザーに読みかけの位置を覚えるときの名前。空なら clone したフォルダーの名前＋「-viewer」を使う。セッションと Mac でフォルダー名がずれないよう、初回の公開で Claude が書き込む | 閲覧ページ |
| `viewer.accent` | 閲覧ページのアクセントの色（`#rrggbb`）。空なら既定の青。暗い表示用の色は自動で作る | 閲覧ページ |
| `note.account_url` | note のアカウントのページ。雛形では空。`/note-publish` が第 1 話の前に尋ねて書く | note の公開（公開後の確認で開く） |
| `note.magazine_url` | 連載マガジンの URL。作ったら書く | note の公開 |
| `note.intro_url` | 導入記事（あらすじ・登場人物・制作方針）の URL。公開したら書く | note の公開 |
| `note.hashtags` | 各話に共通で付けるハッシュタグ | note の公開 |
| `note.publish_schedule` | 予約公開の基本の曜日と時刻（例：「毎週月曜 0:30（日本時間）」） | note の公開 |
| `note.start_after_all_chapters` | `true` なら、全章を書き終えるまで連載を始めない | note の公開 |

## 字数の測り方

- `python3 tools/count_chars.py <ファイル> --target <目安字数>` を使う。ファイル全体から半角スペース・タブ・改行を除いた文字数を数える。
- `tr -d ' \n\r\t' | wc -m` は、ロケールによってバイト数を返し、字数が約 3 倍に見える。使わない。
- 字数を書くのは `plot/outline.md` の「進捗」の表だけ（初稿字数と最終字数）。`log/continuity.md` には書かない。
- `--scenes` を付けると、`---` で区切った場面ごとの字数も出る。場面の配分と比べるときに使う。

## 原稿閲覧ページ

- `tools/build_viewer.py` が `chapters/` から 1 枚の HTML を作り、Claude が Artifact として公開する。手順はスクリプト冒頭の説明にある。
- 縦書き・横書きの切り替え、行番号、行への移動（`#ch3-L17` のような URL でも開ける）、直近の修正箇所の表示ができる。
- 表示する字数は `tools/count_chars.py` と同じ数え方なので、`plot/outline.md` の最終字数と一致する。
- 原稿チェックでは、ここの行番号で「〇行目」と指摘する。行番号は本文ファイルの行番号と同じなので、そのまま直せる。

## 公開（note）

- 書き出し：`/note-export <章番号>` が `publish/note/NN_章題.txt` を作る。本文は書き換えない。
- 投稿：`/note-publish <章番号>` がブラウザーで note に下書きを作り、設定と表示を確かめ、ユーザーの確認を取ってから予約・公開する。公開後の導線（前話・次話のリンク、導入記事の一覧、マガジン）も整える。
- 定型とチェックリストは [publish/note/template.md](../publish/note/template.md)、見出し画像の方針は [publish/note/cover-image.md](../publish/note/cover-image.md) にある。

## 私家版

公開前に通しで読んでもらう一冊は `/build-book` で作る。`dist/` に EPUB と HTML ができる。`dist/` はコミットしない。

## 構成改稿

`/start-revision <版名>` で始める。改稿用のブランチを作り、`docs/templates/` の型を `docs/revision/` に写し、改稿前の記録を `log/archive/`・`bible/archive/`・`plot/archive/` に移す。
そのあと、設計書 → 章別改稿マップ → 章ごとの詳細設計 → 書き直し、の順に進める。
全章を書き直したら `/start-revision` の「改稿を終えるとき」の手順で `docs/revision/` を `docs/archive/<版名>/` へ移してから、`main` に取り込む。
`docs/revision/` がある間は「改稿中」として扱われ、既存の章を書き直せる状態になるため。
