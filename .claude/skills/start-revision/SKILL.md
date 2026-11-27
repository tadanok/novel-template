---
name: start-revision
description: 構成改稿を始める。改稿用のブランチを作り、設計文書の型を docs/revision/ に写し、改稿前の継続性ログと正典の写しを archive/ へ移して、設計書の対話に入る。ユーザーが「構成から直したい」「改稿を始めたい」と言ったとき、または /start-revision が呼ばれたときに使う。
---

# 構成改稿の開始

版名： $ARGUMENTS（例：`v2`。指定がなければユーザーに尋ねる）

## 0. 前提を確かめる

- 改稿の動機と、変えないもの（結末、規模など）をユーザーから聞き取る。
- 作業ツリーに未コミットの変更がないことを確かめる。
- `docs/revision/` がすでにある場合は、進行中の改稿がある（終えた改稿は `docs/archive/` に移っている）。続きなのか、前の改稿を終え忘れたのかを確認する。

## 1. ブランチを作る

`main`（または指定されたブランチ）から `revision/<版名>` を作る。
`main` へ取り込む時期をユーザーに確認し、`plot/open_questions.md` に書く
（公開中の作品なら、公開がすべて終わってから取り込むのが既定）。

## 2. 改稿前の記録を保管場所へ移す

継続性ログの肥大化と、改稿前と改稿後の記録の取り違えを防ぐため、次を行う。

1. `log/continuity.md` を `log/archive/continuity_<改稿前の版名>.md` へ移す（`git mv`）。
   改稿前の版名は、初めての改稿なら `v1`。
2. `bible/` と `plot/` の現在のファイルを、`bible/archive/<改稿前の版名>/`・`plot/archive/<改稿前の版名>/` へ**写す**（`cp`）。
   正典そのものは残し、改稿の設計が決まるたびに書き換える。写しは参照用で、正典ではない。
3. `log/continuity.md` を新しく作る。冒頭の説明は雛形のもの（`log/continuity.md` の先頭部分）と同じにし、
   「この版は `<版名>`。改稿前の記録は `log/archive/continuity_<改稿前の版名>.md`」と 1 行添える。
4. `novel.config.json` の `viewer.label` を `改稿版` などにするか、ユーザーに確認する。

`plot/open_questions.md` の「確定した事項」が長い場合は、改稿前のものを写しの側だけに残し、正典から消してよいか確認する。

## 3. 設計文書の型を写す

`docs/templates/revision_design.md` と `docs/templates/chapter_revision_map.md` を `docs/revision/` へ写し、
`{{作品名}}` を `novel.config.json` の `title` に置き換える。

## 4. commit して、設計の対話に入る

1. ここまでを 1 つのコミットにして、`revision/<版名>` を push する。
2. `docs/revision/revision_design.md` を節ごとに対話で埋める。改稿前の本文と記録（archive）を読んで、問題点と案を示す。
   選択肢は推奨つきで示し、ユーザーの確認を取った節に確認日を書く。
3. 設計書の確認が済んだら、`chapter_revision_map.md` を作る。
4. 設計とマップに合わせて `bible/`・`plot/` を書き換える。

## 5. 報告

- 作ったブランチと、移した・写したファイル
- 設計書の進み具合と、次に決めること
- 書き直しに入るときの依頼文（`docs/prompts/chapter-session.md` の「章の執筆のセッション」。ブランチは `revision/<版名>`）

## 改稿を終えるとき

全章の書き直しが済み、`main` へ取り込む前に行う。ユーザーが「改稿を終える」「main に取り込む」と言ったときに、このスキルの続きとして使う。
`docs/revision/` がある間は「改稿中」として扱われ、`/write-chapter` が既存の章を書き直せる状態になるため、必ず片づける。

1. `plot/outline.md` の進捗で、全章が書き直し済みであること、`plot/open_questions.md` に改稿の未確定事項が残っていないことを確かめる。
2. `docs/revision/` を `docs/archive/<版名>/` へ移す（`git mv`）。設計文書は改稿の経緯として残すが、改稿中の判定からは外れる。
3. `novel.config.json` の `viewer.label` を、改稿前の値（多くは空）に戻すか、ユーザーに確認する。
4. ここまでを 1 つのコミットにして push する。
5. `main` への取り込み（プル リクエストかマージ）は、`plot/open_questions.md` に書いた時期に合わせて、ユーザーの確認を取ってから行う。
