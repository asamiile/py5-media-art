---
name: create-artwork
description: "py5を使ったメディアアート作品を自律的に制作する。CLAUDE.mdのワークフローに従い、ブランチ作成→過去作品調査→実装→コミット→プッシュを行う。Triggers: 作品を作る, create artwork, new sketch, media art"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Skill

CLAUDE.md に記載されたワークフローに従い、py5メディアアート作品を自律的に制作する。

## Workflow

1. `CLAUDE.md` を読んでワークフローを確認する
2. `sketch/WORKS.md` を読んで過去作品を把握する
3. `git checkout -b feature/works-YYYYMMDD` でブランチ作成
4. 過去と重複しない新しい作品を `sketch/{作品名}/main.py` に実装
5. `sketch/WORKS.md` を更新
6. コミット・プッシュ

## Notes

- 必ず過去作品と異なるコンセプト・技法を選ぶ
- ファイル名は `main.py` 固定
- 作品名はスネークケース
