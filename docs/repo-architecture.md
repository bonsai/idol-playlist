# Loosely Coupled Repository Architecture

各 repository を「機能を持つ tool」として扱い、Python module を共有するのではなく、**入力・出力の契約を共有**する。

## Repositories

| repo | role | primary output |
|---|---|---|
| [idol-research](https://github.com/bonsai/idol-research) | 観測・調査 | observations / corpus |
| [idol-playlist](https://github.com/bonsai/idol-playlist) | 集計・ranking・playlist | weekly / monthly / playlist |
| [music-bigdata](https://github.com/bonsai/music-bigdata) | DS / ML / BQML | features / models / insights |

## Boundary

```
idol-research
    │
    │ observations.json
    ▼
idol-playlist
    │
    ├── ranking
    ├── weekly aggregate
    ├── monthly aggregate
    │
    │ analysis-ready JSON/CSV
    ▼
music-bigdata
    │
    ├── EDA
    ├── feature engineering
    ├── ML / BQML
    └── marketing analysis

music-bigdata ── analysis result ──► idol-playlist
```

依存方向を固定せず、**artifactを介して疎結合**にする。

## Tool sharing rule

各 repo の `tools.yaml` が、その repo が外部に提供する tool の契約である。

- tool は input / output を明示する
- JSON を基本交換形式にする
- 他 repo の Python code を import しない
- 内部実装を変更しても contract を維持すればよい
- GitHub raw file / artifact / API のどれでも consumer になれる

つまり、

```
repo A
  └─ tools.yaml
       ↓ contract
repo B
  └─ input.json
       ↓
     tool
       ↓
     output.json
```

とする。

## 集計の位置づけ

`idol-playlist` に既にある KPI / weekly / monthly 集計は、playlist の内部ロジックとして閉じ込めず、**aggregate tool** として公開する。

特に `KPI.yaml` の score は「楽曲の良さ」ではなく、このプロジェクトで観測する関心度指標なので、DS 側では別の feature として扱える。

## GA4 / BigQuery / BQML

将来の marketing / advertising-effect analysis では、

```
GA4
 ↓
BigQuery
 ↓
music-bigdata / BQML
 ↓
analysis artifact
```

とし、`idol-playlist` が GA4 や BQML に直接依存する必要はない。

## Canon

- **GitHub = canon**
- **repo = boundary**
- **tools.yaml = interface**
- **JSON/CSV = data contract**
- **AW = execution**
- **artifact = repository間の交換物**

「共有する」のはコードではなく、**tool と data の interface**。
