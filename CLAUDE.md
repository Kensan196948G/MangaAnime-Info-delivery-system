# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## システム詳細仕様書：アニメ・マンガ最新情報配信システム

### 1. 概要

本システムは、ClaudeCodeおよびClaude-flowのAgent機能（SubAgent機能）を活用し、最大10体程度のSubAgentによる並列開発・分担実装を行うことを前提とした、アニメ・マンガの新作情報を自動で収集し、指定ユーザーへGmailで通知し、Googleカレンダーに登録する自動配信システムである。n8n等のワークフローエンジンは利用せず、Pythonスクリプトとスケジューラで構成する。

---

### 2. システム構成

| 機能カテゴリ   | 技術構成                        |
| -------- | --------------------------- |
| 情報収集     | Python（API・RSS）             |
| フィルタリング  | Pythonロジック（NGワード）           |
| データ保存    | SQLite                      |
| 通知       | Gmail API（OAuth2）           |
| カレンダー登録  | Google Calendar API（OAuth2） |
| スケジューリング | cron（Linux環境前提）             |
| ログ管理     | Python loggingモジュール         |

---

### 3. 機能仕様

#### 3.1 情報収集（収集レイヤ）

##### アニメ：

* **AniList GraphQL API**

  * 放送予定、配信プラットフォーム、作品タイトルを取得
  * 無料（1分あたり90リクエスト制限）
* **しょぼいカレンダーAPI**

  * 日本国内のTV放送枠に対応
  * JSON形式で日付・局・タイトルを取得

##### マンガ：

* **出版社/電子書籍ストアの公式RSS**

  * BookWalker, マガポケ, ジャンプBOOKストア, 楽天Kobo等
  * タイトル、巻数、URL、配信日をRSSで取得

##### 配信先：

* **dアニメストア公式RSS**（[https://anime.dmkt-sp.jp/animestore/CF/rss/）](https://anime.dmkt-sp.jp/animestore/CF/rss/）)
* **Amazon Prime / Netflix**

  * AniList GraphQL APIから"streamingEpisodes"フィールドを通じて各作品に付随する配信プラットフォーム情報（例：Netflix、Amazon Primeなど）を取得可能。該当作品の放送日時や話数情報とともに取得できるため、公式APIがないこれらプラットフォームの代替手段として有効。 公式APIは非公開のため、AniListの"streamingEpisodes"情報から推定

---

#### 3.2 データ整形・正規化（正規化レイヤ）

* 各ソースから取得したデータを共通形式に変換
* `work_id` / `release_id`をハッシュ生成で一意に管理

##### SQLiteテーブル定義：

```sql
CREATE TABLE works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  title_kana TEXT,
  title_en TEXT,
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE releases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date)
);
```

---

#### 3.3 フィルタリング（ロジックレイヤ）

* NGワード一覧に一致する作品を除外

```python
NG_KEYWORDS = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"]
```

* AniListの`genres`, `tags`, `description`も対象

---

#### 3.4 通知処理（配信レイヤ）

* **Gmail API**により自分のアドレスにHTMLメール送信

  * OAuth2認証を使用（`token.json`管理）
  * HTML本文に作品画像・タイトル・配信日・URL等を記載

* **Google Calendar API**により予定を追加

  * タイトル例：「作品名 第3話配信」「作品名 第5巻発売」
  * カレンダーID：primary

---

#### 3.5 スケジューラ構成

本システムはLinux（Ubuntu）環境を前提とし、cronによるスケジューリングを行う。

##### Ubuntu：

* crontabに以下を登録（毎朝08:00にPythonスクリプトを実行）

```bash
0 8 * * * python3 release_notifier.py
```

---

### 4. モジュール構成例

```
./
├── config.json
├── release_notifier.py
├── modules/
│   ├── anime_anilist.py
│   ├── manga_rss.py
│   ├── filter_logic.py
│   ├── db.py
│   ├── mailer.py
│   └── calendar.py
└── db.sqlite3
```

---

### 5. 拡張機能（オプション）

* Claudeによるあらすじ生成
* Web UI（Flask + Bootstrap）
* Googleスプレッドシート連携
* カレンダーのジャンル別色分け

---

### 6. 実行サイクル

| 時間        | 内容                            |
| --------- | ----------------------------- |
| 毎朝08:00   | 情報収集 → DB更新 → メール通知 → カレンダー登録 |
| 随時（オプション） | あらすじ自動生成                      |

---




### 📘 ClaudeCode＋Agent＋Claude-flowベースの構成一式

# ✅ Claude並列開発実行コマンド

## 推奨実行方法
```bash
# 自動スクリプトで実行（推奨）
./run_claude_autoloop.sh

# または Makefileで実行
make claude-flow
```

## 直接実行
```bash
claude --dangerously-skip-permissions \
       "CLAUDE.mdの仕様に従って5体のAgentで並列開発してください"
```

## 安全モード実行
```bash
claude "CLAUDE.mdの仕様を確認してプロジェクト構造を理解してください"
```

---

# 📁 ディレクトリ構成（推奨）

```
project-root/
├── .claude/agents/              # 各Agent定義ファイル
│   ├── MangaAnime-CTO.md
│   ├──MangaAnime-DevUI.md
│   ├── MangaAnime-DevAPI.md
│   ├── MangaAnime-QA.md
│   └── MangaAnime-Tester.md
├── docs/                        # 仕様・設計ドキュメント群
│   └── system_spec.md
├── workflows/                   # ClaudeFlowワークフロー定義
│   └── batch.yaml
├── settings.local.json          # 権限・環境設定
└── run_claude_autoloop.sh       # 自動ループ実行用スクリプト
```

---

# 🔧 agents.yaml（Claude-flow YAML定義形式）

```yaml
agents:
  - id: agent-Recipe-CTO
    goal: システム全体の方針・レビュー・構成設計
    role: CTO
    description: 全エージェントの作業結果を統合・レビューし、アーキテクチャ判断を行う。

  - id: agent-Recipe-DevUI
    goal: UIコンポーネントをReactで構築
    role: フロントエンド開発者
    description: FigmaやHTML設計をベースにUIを構築、アクセシビリティにも配慮。

  - id: agent-Recipe-DevAPI
    goal: API設計とFlask実装
    role: バックエンド開発者
    description: UIと連携するREST API群をFlaskで実装し、テストも含めて担当。

  - id: agent-Recipe-QA
    goal: UX/用語統一/セキュリティレビュー
    role: QA担当
    description: 各エージェントの成果物に対してアクセシビリティ・表記揺れ・ガイドライン準拠性を確認。

  - id: agent-Recipe-Tester
    goal: 自動テスト生成と実行（Playwright）
    role: テストエンジニア
    description: 開発されたUI/APIに対し、E2Eおよび回帰テストスクリプトを自動生成・実行。
```

---

# ⚙️ settings.local.json（ClaudeCode用設定）

```json
{
  "permissions": {
    "allow": [
      "Bash(mkdir:*)",
      "Bash(touch:*)",
      "Bash(cp:*)",
      "Python(open:*)"
    ],
    "deny": []
  }
}
```

---

# 🔁 run_claude_autoloop.sh（自動ループ実行スクリプト）

```bash
#!/bin/bash

echo "🔄 ClaudeFlow自動ループを開始します..."
npx claude-flow mcp start \
  --target 0:claude:@agent-Recipe-CTO \
  --target 1:claude:@agent-Recipe-DevUI \
  --target 2:claude:@agent-Recipe-DevAPI \
  --target 3:claude:@agent-Recipe-QA \
  --target 4:claude:@agent-Recipe-Tester \
  --file "./docs/*.md" \
  --mode full-auto \
  --max-iterations 5 \
  --dangerously-skip-permissions
```

---

# 🧠 備考
- `.md`ドキュメントに **役割ごとの期待成果物・制約条件・連携要件** を明記することが重要です。
- `agents.yaml`と`.claude/agents/*.md`は併用可能（Claude側が優先読み込み）。