# py5 Media Art — Claude Code Instructions

## Project Overview

py5を使ったメディアアート作品を自律的に制作するリポジトリ。

## Autonomous Artwork Creation Workflow

作品を自律的に作る際は、以下の手順を厳守すること。

### Step 1: ブランチを作成する

```bash
git checkout main
git pull origin main
git checkout -b feature/works-$(date +%Y%m%d)
```

### Step 2: 過去作品を調査する

- `sketch/WORKS.md` を必ず読み、過去の作品一覧・テーマ・技法を把握する
- `sketch/` 配下の既存コードも参照して、同じアイデアの繰り返しを避ける
- **過去と同じコンセプト・ビジュアル・アルゴリズムの作品は作らない**

### Step 3: 新しい作品を実装する

- `sketch/{作品名}/main.py` に作品を実装する
  - 作品名はスネークケース（例: `flowing_particles`, `recursive_tree`）

#### サイズ設定

| モード | 解像度 | 用途 |
|---|---|---|
| Preview | 1920×1080 | スケッチ確認・スクショ保存 |
| Output | 3840×2160 | UE / TouchDesigner 出力用 |

- スクショ保存は **Previewモード** で行う
- Outputモードへの切り替えは `SIZE = OUTPUT_SIZE` の1行変更のみ

#### py5 コーディング規約

```python
from pathlib import Path
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120  # 約2秒後（60fps）にプレビュー保存して終了

PREVIEW_SIZE = (1920, 1080)  # 16:9 preview
OUTPUT_SIZE  = (3840, 2160)  # 4K output for UE / TouchDesigner

SIZE = PREVIEW_SIZE  # ← switch to OUTPUT_SIZE for final export

def setup():
    py5.size(*SIZE)
    py5.background(0)

def draw():
    # フレームごとの描画処理
    pass

    # --- 末尾に必ず記述 ---
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()

py5.run_sketch()
```

- `py5.run_sketch()` で実行
- `background()` は毎フレーム呼ぶかどうかを意図的に選択する（軌跡を残したいなら呼ばない）
- `SKETCH_DIR / "preview.png"` に自動保存 → 自動終了する設計にする
- 乱数シードは固定しない（毎回異なる結果にする）

### Step 4: プレビューを起動してスクショを保存する

```bash
uv run python sketch/{作品名}/main.py
```

- スケッチが自動的に `sketch/{作品名}/preview.png` を保存して終了する
- 保存されたことを確認する（ファイルが存在するか `ls sketch/{作品名}/` で確認）

### Step 4.5: 批評者レビュー（Artist → Critic → Artist ループ）

**批評者** (`.agents/skills/critic/SKILL.md`) として以下を評価する：

1. `sketch/WORKS.md` で過去作品との差異を確認
2. `sketch/{作品名}/main.py` のコードを読む
3. `sketch/{作品名}/preview.png` を視覚的に評価する
4. 4軸（独自性・視覚的インパクト・技法・コンセプト）でスコアリング

**Verdict が `REVISE` の場合：**
- **アーティスト** (`.agents/skills/artist/SKILL.md`) としてフィードバックを元に修正する
- `uv run python sketch/{作品名}/main.py` を再実行して `preview.png` を更新する
- 批評者が再評価する
- このループは **最大2回** まで。3回目は必ず `APPROVE` とする

**Verdict が `APPROVE` の場合：**
- 次のステップへ進む

### Step 5: 作品の README.md を作成する

`sketch/{作品名}/README.md` を以下の形式で作成する：

```markdown
# {Work Title in English}

![preview](preview.png)

{Description in English. Around 200 characters. Include theme, technique, and highlights.}
```

### Step 6: WORKS.md を更新する

`sketch/WORKS.md` に作品情報を追記する：

```markdown
## {work_name}

- **Date**: YYYY-MM-DD
- **Theme**: (e.g. fluid, geometry, nature)
- **Technique**: (e.g. particle system, recursion, noise)
- **Description**: One-line summary in English
```

### Step 7: コミットする

```bash
git add sketch/{作品名}/
git add sketch/WORKS.md
git commit -m "feat: add {作品名} sketch"
```

### Step 8: プッシュする

```bash
git push -u origin feature/works-$(date +%Y%m%d)
```

### Step 9: .agents/ の更新（必要な場合）

新しいスキルや設定が必要になった場合は `.agents/skills/` を更新する。

## Directory Structure

```
sketch/
  WORKS.md                  # 全作品の台帳（必ず更新する）
  {作品名}/
    main.py                 # エントリポイント（固定）
    preview.png             # スケッチ実行時に自動生成
    README.md               # 作品説明
.agents/
  skills/
    create-artwork/         # 作品生成スキル
    artist/                 # アーティストエージェント
    critic/                 # 批評者エージェント
```

## Running a Sketch

```bash
uv run python sketch/{作品名}/main.py
```
