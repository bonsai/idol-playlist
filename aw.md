# AW — idol-playlist

## Purpose

`aw` は `idol-playlist` の実行入口である。

GitHub Actions から実行要求を受けた場合も、実処理は `aw` に集約する。

```
GitHub Actions
      ↓
     GATE
      ↓
      AW
      ↓
  LangGraph
      ↓
    collect
      ↓
 LLM review（必要時）
      ↓
     rank
      ↓
 weekly TOP 10
      ↓
 monthly aggregate
      ↓
 youtube-match
      ↓
   playlist
```

## Principle

- Workflow は実行条件と権限を管理する。
- GATE は実行可能性を検証する。
- AW は実処理を担当する。
- LangGraph は処理フローを管理する。
- Django はデータ/API/Admin を担当する。
- BigQuery / BQML は蓄積・分析を担当する。
- YouTube Data API はプレイリスト同期を担当する。

Workflow に業務ロジックを直接書かず、`aw` に集約する。

## Commands

```bash
aw collect
aw rank
aw youtube-match
aw playlist
aw run
```

通常運用では `aw run` を使用する。

## Full Run

`aw run` は以下を順番に実行する。

```
collect
  ↓
LLM review（必要時のみ）
  ↓
rank
  ↓
weekly
  ↓
monthly
  ↓
persist
  ↓
youtube-match
  ↓
playlist
```

LLM は常時実行ではなく、データ判定が必要な場合の分岐として扱う。

## Weekly

毎週の実行では、その週のランキングから TOP 10 を生成する。

```
data/weekly/YYYY-Www.json
```

週次データは過去分を削除せず、履歴として蓄積する。

## Monthly

週次データを集計して月間ランキングを生成する。

```
data/monthly/YYYY-MM.json
```

月間集計では少なくとも以下を保持する。

```yaml
appearances:
score_total:
average_score:
best_rank:
ask_count:
lyrics_view:
youtube_view:
monthly_rank:
```

## Ranking

日次ランキングは以下に保存する。

```
data/rankings/YYYY-MM-DD.jsonl
```

ランキングの `score` は楽曲の「良さ」ではない。

このプロジェクトでは、どれだけ聞かれ、探され、質問されたかを観測するためのプロジェクト指標として扱う。

## YouTube

ランキングされた楽曲について YouTube の候補動画を照合する。

結果は以下に保存する。

```
data/youtube/playlist.json
```

プレイリストでは動画ID、楽曲名、アイドル名、ランク、スコアを扱い、重複除去と非公開・削除動画の再照合を行う。

## GitHub Actions

GitHub Actions は `aw` の代替実装ではない。

```
Actions = trigger / gate / environment
AW      = execution
```

Workflow からは、

```yaml
- run: aw run
```

として実行する。

## GATE

AW の前に GATE を通す。

GATE では少なくとも以下を確認する。

```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py migrate --noinput
aw run
test -f data/youtube/playlist.json
test -s data/youtube/playlist.json
```

GATE が失敗した場合、後続処理を実行しない。

## Local

開発時はローカルから直接実行できる。

```bash
cd ~/idol-playlist
source .venv/bin/activate
aw run
```

AW はローカル実行を基本とする。

GitHub Actions は定期実行・検証・公開のために使用する。

## Data Flow

```
history
   ↓
latest
   ↓
now
   ↓
AW
   ↓
action
```

生成物は GitHub 上に履歴として保存し、次回の観測・集計に利用する。

## Repository Boundary

### idol-playlist

- 楽曲カタログ
- 聞かれる曲ランキング
- 週次 TOP 10
- 月間集計
- YouTube 動画照合
- プレイリスト

### idol-research

- 地下アイドル研究
- 情報源
- 調査 corpus
- RQ / RX

### idol-produce-or

- ゲーム
- 選択
- 生成される未来

それぞれの責務を分離し、AW から必要なデータだけを連携する。

## Operational Rule

新しい処理を追加するときは、まず `aw` の workflow に追加する。

Workflow YAML に処理ロジックを直接増やさない。

```
❌ YAML → 独自処理

⭕ YAML → GATE → AW → LangGraph
```

これにより、ローカル実行と GitHub Actions 実行で同じ処理系を利用する。
