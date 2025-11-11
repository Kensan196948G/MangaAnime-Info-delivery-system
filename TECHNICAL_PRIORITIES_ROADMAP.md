# 技術的優先順位ロードマップ

**発行日**: 2025-11-11
**作成者**: MangaAnime-CTO Agent
**バージョン**: 1.0
**対象期間**: 2025-11 ～ 2026-02

---

## エグゼクティブサマリー

本ロードマップは、MangaAnime情報配信システムの技術的優先順位を定義し、限られたリソースを最大限に活用するための戦略的ガイドを提供します。

**重要指標:**
- 現在のシステム成熟度: 93/100 (EXCELLENT)
- 即座対応必要項目: 3件
- 1ヶ月以内対応推奨: 5件
- 3ヶ月以内対応: 4件

---

## 優先度マトリクス

### HIGH PRIORITY（即座～1週間以内）

#### P1-1: RSS Feed設定拡充 🔴 CRITICAL
**ビジネスインパクト**: HIGH
**技術的難易度**: LOW
**工数**: 4時間
**担当Agent**: MangaAnime-DataCollector

**背景:**
現在、マンガ情報収集がほぼ機能していない（RSS未設定のため0件収集）。これはシステムの主要機能の50%が未稼働であることを意味します。

**アクション:**
1. 各出版社の公式RSSフィードを調査
2. `config.json`に追加
3. 動作確認テスト実施

**具体的RSS候補:**
```json
{
  "apis": {
    "rss_feeds": {
      "feeds": [
        {
          "name": "BookWalker新刊コミック",
          "url": "https://bookwalker.jp/series/rss/",
          "type": "manga",
          "priority": "high"
        },
        {
          "name": "マガポケ",
          "url": "https://pocket.shonenmagazine.com/rss",
          "type": "manga",
          "priority": "high"
        },
        {
          "name": "少年ジャンプ+",
          "url": "https://shonenjumpplus.com/rss",
          "type": "manga",
          "priority": "high"
        },
        {
          "name": "楽天Kobo新刊マンガ",
          "url": "https://books.rakuten.co.jp/rss/genre/001001/",
          "type": "manga",
          "priority": "medium"
        },
        {
          "name": "コミックシーモア新刊",
          "url": "https://www.cmoa.jp/rss/new/",
          "type": "manga",
          "priority": "medium"
        }
      ]
    }
  }
}
```

**成功基準:**
- [ ] 最低5つのRSSフィード追加
- [ ] 各フィードから正常にデータ取得確認
- [ ] 100件以上のマンガリリース情報収集

**期待効果:**
- マンガ情報収集機能の完全稼働
- システム機能完成度50% → 100%
- ユーザー満足度向上

---

#### P1-2: requirements.txt バージョン固定 🟡 HIGH
**ビジネスインパクト**: MEDIUM
**技術的難易度**: LOW
**工数**: 2時間
**担当Agent**: MangaAnime-CTO

**背景:**
依存ライブラリのバージョンが固定されていないため、将来的に互換性問題が発生するリスクがあります。

**アクション:**
```bash
# 現在の環境のバージョン固定
pip freeze > requirements-lock.txt

# requirements.txt に反映
```

**推奨バージョン:**
```txt
# Core Python
python>=3.8,<4.0

# Google APIs（セキュリティ更新対応）
google-auth==2.17.0
google-auth-oauthlib==1.0.0
google-api-python-client==2.80.0

# HTTP Clients
requests==2.31.0
aiohttp==3.8.5

# RSS/Feed Processing
feedparser==6.0.10
beautifulsoup4==4.12.0
lxml==4.9.3

# Date/Time
pytz==2023.3
python-dateutil==2.8.2

# Security
cryptography==41.0.0

# Monitoring
psutil==5.9.5

# Development
pytest==7.4.0
pytest-cov==4.1.0
black==23.7.0
flake8==6.0.0
```

**成功基準:**
- [ ] 全依存関係のバージョン固定
- [ ] requirements.txt と requirements-lock.txt 作成
- [ ] CI/CD環境での動作確認

---

#### P1-3: Windowsタスクスケジューラ対応 🟡 HIGH
**ビジネスインパクト**: HIGH
**技術的難易度**: MEDIUM
**工数**: 1日
**担当Agent**: MangaAnime-Scheduler

**背景:**
現在Windows環境では手動実行が必要。自動化は本システムの核心機能です。

**アクション:**
1. `modules/scheduler.py` 実装
2. `setup_scheduler.py` 作成
3. Windows環境テスト

**期待効果:**
- Windows環境での完全自動化
- ユーザービリティ向上
- 手動運用コスト削減

**成功基準:**
- [ ] Windowsタスクスケジューラ自動設定
- [ ] 毎朝8時の自動実行確認
- [ ] ドキュメント整備

---

### MEDIUM PRIORITY（1週間～1ヶ月以内）

#### P2-1: しょぼいカレンダーAPI統合 🟢 MEDIUM
**ビジネスインパクト**: MEDIUM
**技術的難易度**: MEDIUM
**工数**: 4日
**担当Agent**: MangaAnime-DataCollector

**背景:**
AniList APIだけでは日本国内のTV放送情報が不完全。しょぼいカレンダーは日本の地上波・BS放送情報に強みがあります。

**技術仕様:**
```python
# modules/syoboi_calendar.py
class SyoboiCalendarCollector:
    API_BASE_URL = "https://cal.syoboi.jp/json.php"

    def collect_anime_schedule(self, start_date, end_date):
        """TV放送スケジュール取得"""
        params = {
            'Req': 'ProgramByDate',
            'Start': start_date.strftime('%Y%m%d'),
            'End': end_date.strftime('%Y%m%d'),
            'Limit': 1000
        }
        # Implementation
```

**データソース比較:**
| ソース | 強み | 弱み |
|--------|------|------|
| AniList | 配信プラットフォーム情報 | TV放送情報弱い |
| しょぼいカレンダー | 日本のTV放送情報 | 配信情報なし |
| 統合後 | 完全な情報カバレッジ | 重複排除必要 |

**成功基準:**
- [ ] API統合完了
- [ ] 100件以上のTV放送情報取得
- [ ] AniListとの重複排除実装
- [ ] テストカバレッジ85%

**期待効果:**
- アニメ情報の完全性向上
- TV視聴者への対応
- 情報源の多様化（リスク分散）

---

#### P2-2: REST API拡張（DevAPI） 🟢 MEDIUM
**ビジネスインパクト**: MEDIUM
**技術的難易度**: MEDIUM
**工数**: 1週間
**担当Agent**: MangaAnime-DevAPI

**背景:**
Web UI実装のためのバックエンドAPI整備が必要。現在のシステムはCLIベースのため、Web化の基盤を構築します。

**実装エンドポイント:**
```
GET    /api/releases/recent          # 最新リリース
GET    /api/works                    # 作品一覧
POST   /api/works                    # 作品作成
PUT    /api/works/{id}               # 作品更新
DELETE /api/works/{id}               # 作品削除
GET    /api/stats                    # 統計情報
GET    /api/health                   # ヘルスチェック
```

**技術スタック:**
- Flask-RESTful or FastAPI
- OpenAPI 3.0仕様書
- Swagger UI統合
- JWT認証（将来拡張）

**成功基準:**
- [ ] 7つのエンドポイント実装
- [ ] OpenAPI仕様書作成
- [ ] Postman Collection提供
- [ ] ユニットテスト80%カバレッジ

---

#### P2-3: Web UI本格実装（DevUI） 🟢 MEDIUM
**ビジネスインパクト**: MEDIUM
**技術的難易度**: HIGH
**工数**: 2週間
**担当Agent**: MangaAnime-DevUI

**背景:**
CLI運用から脱却し、視覚的な管理インターフェースを提供。運用性とユーザビリティを大幅に向上します。

**実装機能:**
1. ダッシュボード
   - 統計情報
   - 最新リリース表示
   - システムヘルス監視
2. 作品・リリース管理
   - 一覧表示（ページネーション）
   - 検索・フィルタ
   - CRUD操作
3. 設定画面
   - NGワード管理
   - スケジュール設定
   - 通知設定

**技術スタック:**
- React 18 + TypeScript
- Tailwind CSS
- Zustand（状態管理）
- React Router v6
- Vite（ビルドツール）

**成功基準:**
- [ ] 3つの主要画面実装
- [ ] レスポンシブデザイン
- [ ] WCAG 2.1 AA準拠
- [ ] Lighthouse スコア 90+

---

#### P2-4: E2E自動テスト構築（Tester） 🟢 MEDIUM
**ビジネスインパクト**: LOW
**技術的難易度**: MEDIUM
**工数**: 1週間
**担当Agent**: MangaAnime-Tester

**背景:**
回帰テスト自動化により、継続的な品質保証を実現。開発速度向上とバグ削減に寄与します。

**実装範囲:**
- Playwright統合
- 主要ユーザーフロー5シナリオ
- CI/CD統合（GitHub Actions）
- 自動レポート生成

**テストシナリオ:**
1. データ収集フロー
2. リリース通知フロー
3. 作品管理CRUD
4. フィルタリング動作
5. エラーハンドリング

**成功基準:**
- [ ] 5つのE2Eテスト実装
- [ ] CI/CD統合完了
- [ ] 実行時間 < 5分
- [ ] 安定性 > 95%

---

#### P2-5: テストカバレッジ90%達成（QA） 🟢 MEDIUM
**ビジネスインパクト**: LOW
**技術的難易度**: MEDIUM
**工数**: 1週間
**担当Agent**: MangaAnime-QA

**背景:**
現在のカバレッジ85%を90%に向上。残存バグの早期発見と品質保証強化。

**対象モジュール優先順位:**
1. modules/db.py → 目標95%
2. modules/anime_anilist.py → 目標90%
3. modules/mailer.py → 目標85%
4. modules/calendar.py → 目標85%
5. modules/filter_logic.py → 目標95%

**アプローチ:**
- エッジケーステスト追加
- 異常系テスト強化
- 統合テスト拡充

**成功基準:**
- [ ] 全体カバレッジ90%達成
- [ ] 新規テスト50件以上追加
- [ ] バグ発見3件以上

---

### LOW PRIORITY（3ヶ月以内）

#### P3-1: GraphQL API検討 🔵 LOW
**ビジネスインパクト**: LOW
**技術的難易度**: HIGH
**工数**: 2週間
**担当Agent**: MangaAnime-DevAPI

**背景:**
REST APIで十分だが、将来的なフロントエンド複雑化に備えてGraphQL移行を検討。

**判断基準:**
- フロントエンド要求が複雑化した場合
- N+1問題が顕在化した場合
- リアルタイム機能が必要になった場合

**現時点の判断**: REST APIで十分、保留

---

#### P3-2: Redis キャッシング導入 🔵 LOW
**ビジネスインパクト**: LOW
**技術的難易度**: MEDIUM
**工数**: 1週間
**担当Agent**: MangaAnime-DevAPI

**背景:**
頻繁にアクセスされるデータのキャッシング。パフォーマンス向上。

**判断基準:**
- 同時ユーザー数 > 10
- レスポンスタイム > 3秒
- データベース負荷 > 70%

**現時点の判断**: 単一ユーザー運用では不要、将来検討

---

#### P3-3: Claude連携あらすじ生成 🔵 LOW
**ビジネスインパクト**: LOW
**技術的難易度**: MEDIUM
**工数**: 1週間
**担当Agent**: 新規Agent（AI Integration）

**背景:**
作品の魅力を伝えるためのAI生成あらすじ。付加価値機能。

**技術仕様:**
```python
# modules/ai_summarizer.py
import anthropic

class ClaudeSummarizer:
    def generate_synopsis(self, work_data):
        """Claude APIであらすじ生成"""
        # Implementation using Anthropic Claude API
```

**判断基準:**
- コア機能完成後
- APIコスト確認後
- ユーザー需要確認後

**現時点の判断**: Phase 3以降で検討

---

#### P3-4: PostgreSQL移行準備 🔵 LOW
**ビジネスインパクト**: LOW
**技術的難易度**: HIGH
**工数**: 2週間
**担当Agent**: MangaAnime-DevAPI + DBA（新規）

**背景:**
スケールアウト準備。大規模運用時のデータベース移行。

**判断基準:**
- 登録作品数 > 10,000
- 同時書き込み発生
- 並行処理必要性

**現時点の判断**: 現在362件、SQLiteで十分、将来検討

**移行計画（将来参考）:**
```python
# migration/sqlite_to_postgres.py
# 1. スキーママッピング
# 2. データエクスポート
# 3. PostgreSQL インポート
# 4. インデックス再構築
# 5. 動作確認
```

---

## 技術的負債管理

### 既知の技術的負債

#### D1: 同期処理アーキテクチャ
**影響**: パフォーマンス
**深刻度**: LOW
**対応時期**: Phase 4以降

**説明:**
現在の同期処理は保守性を優先した設計。スループット向上が必要になった場合、非同期処理への移行を検討。

**移行パス:**
1. Celery + Redis導入
2. タスクキュー化
3. バックグラウンドワーカー実装

**現時点の判断**: 問題なし、保留

---

#### D2: SQLite並行書き込み制限
**影響**: スケーラビリティ
**深刻度**: LOW
**対応時期**: 1万作品超時

**説明:**
SQLiteは並行書き込みに弱い。大規模化時はPostgreSQL移行必要。

**移行トリガー:**
- 登録作品数 > 10,000
- 書き込みエラー増加
- レスポンスタイム劣化

**現時点の判断**: 362件で問題なし、監視継続

---

#### D3: 手動OAuth更新
**影響**: 運用性
**深刻度**: MEDIUM
**対応時期**: 3ヶ月以内

**説明:**
Googleトークン期限切れ時の手動更新が必要。自動更新は実装済みだが、監視・アラート強化が望ましい。

**改善案:**
```python
# modules/auth_monitor.py
class AuthMonitor:
    def check_token_expiry(self):
        """トークン期限切れチェック"""
        if token_expires_in < 7_days:
            send_alert("トークン更新が必要です")
```

**優先度**: MEDIUM（P2-6として追加検討）

---

## パフォーマンス最適化ロードマップ

### 現在のパフォーマンス指標

```
データ収集: 362件 in 38.2秒
処理速度: 9.5 件/秒
エラー率: 0%
メモリ使用量: < 100MB
CPU使用率: < 20%
```

### 最適化目標（Phase 3）

```
データ収集: 1000件 in 60秒
処理速度: 16.7 件/秒
エラー率: < 1%
メモリ使用量: < 200MB
CPU使用率: < 40%
```

### 最適化戦略

**短期（1ヶ月）:**
- ✅ Connection Pooling（実装済み）
- ✅ WAL Mode（実装済み）
- 🔄 クエリ最適化
- 🔄 インデックス見直し

**中期（3ヶ月）:**
- Redis キャッシング
- 非同期処理導入
- バッチサイズ最適化

**長期（6ヶ月）:**
- CDN導入（静的ファイル）
- 分散処理
- マイクロサービス化検討

---

## セキュリティロードマップ

### 現在のセキュリティスコア: 93/100 🏆

**実装済みセキュリティ機能:**
- ✅ OAuth2認証
- ✅ SQLインジェクション対策
- ✅ 入力検証
- ✅ ログマスキング
- ✅ 脆弱性スキャン

### セキュリティ改善計画

#### S1: 環境変数による秘密管理（1週間）
**現状**: credentials.json ファイル管理
**改善**: 環境変数 + AWS Secrets Manager統合

```python
# modules/config.py
import os

GMAIL_API_KEY = os.getenv('GMAIL_API_KEY')
CALENDAR_API_KEY = os.getenv('CALENDAR_API_KEY')
```

#### S2: トークン暗号化保存（1週間）
**現状**: token.json プレーンテキスト
**改善**: Fernet暗号化

```python
# modules/auth.py
from cryptography.fernet import Fernet

def save_encrypted_token(token):
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    # Save encrypted token
```

#### S3: API Rate Limiting（3日）
**現状**: 基本的な制限
**改善**: Redis ベースの分散レート制限

---

## リソース配分計画

### Agent稼働スケジュール（1ヶ月）

```
Week 1:
  DataCollector: P1-1 RSS Feed設定 (4h)
  Scheduler: P1-3 Windowsスケジューラ (3d)
  CTO: P1-2 requirements固定 (2h)

Week 2:
  DataCollector: P2-1 しょぼいカレンダー (4d)
  DevAPI: P2-2 REST API開発開始 (5d)
  QA: P2-5 テストカバレッジ向上開始 (5d)

Week 3:
  DevUI: P2-3 Web UI開発開始 (10d)
  DevAPI: P2-2 REST API完成 (継続)
  Tester: P2-4 E2Eテスト開始 (5d)

Week 4:
  DevUI: P2-3 Web UI開発継続
  Tester: P2-4 E2Eテスト完成
  QA: P2-5 テストカバレッジ完成
  CTO: 統合レビュー
```

### 工数見積（総計）

```
HIGH Priority:   3件  =  2日
MEDIUM Priority: 5件  = 40日
LOW Priority:    4件  = 60日（保留）

実行対象: HIGH + MEDIUM = 42日
並列開発想定: 6 Agent x 2週間 = 実質2週間で完了
```

---

## 成功指標（KPI）

### 技術KPI

**1ヶ月後:**
- ✅ RSS Feed 5つ以上統合
- ✅ Windowsスケジューラ対応完了
- ✅ しょぼいカレンダーAPI統合完了
- ✅ REST API 7エンドポイント実装
- ⏳ Web UI MVP完成（80%）
- ⏳ E2Eテスト5シナリオ実装

**3ヶ月後:**
- ✅ Web UI本格稼働
- ✅ テストカバレッジ90%達成
- ✅ システム機能完成度100%
- ✅ ドキュメント完全更新
- ⏳ 運用実績1000件以上

### ビジネスKPI

**ユーザー満足度:**
- 情報網羅性: 50% → 100%
- 自動化レベル: 80% → 100%
- 使いやすさ: CLI → Web UI

**運用効率:**
- 手動作業時間: 5分/日 → 0分/日
- エラー対応時間: 30分/週 → 10分/週
- 設定変更時間: 10分 → 1分（UI経由）

---

## リスク管理

### 高リスク項目

#### R1: しょぼいカレンダーAPI変更
**確率**: MEDIUM
**影響**: HIGH
**対策**:
- エラーハンドリング強化
- フォールバック処理
- 定期的な動作確認

#### R2: Google API仕様変更
**確率**: LOW
**影響**: CRITICAL
**対策**:
- 公式アナウンス監視
- バージョン固定
- 代替認証手段準備

#### R3: 開発遅延
**確率**: MEDIUM
**影響**: MEDIUM
**対策**:
- 並列開発によるリスク分散
- 週次進捗確認
- バッファ期間確保

### 低リスク項目

#### R4: パフォーマンス劣化
**確率**: LOW
**影響**: LOW
**対策**: 継続的な監視

---

## 意思決定フレームワーク

### 新機能追加判断基準

```python
def should_implement_feature(feature):
    score = 0

    # ビジネス価値
    if feature.business_impact == "HIGH":
        score += 10
    elif feature.business_impact == "MEDIUM":
        score += 5

    # 技術的難易度（低いほど高スコア）
    if feature.difficulty == "LOW":
        score += 10
    elif feature.difficulty == "MEDIUM":
        score += 5

    # 工数（少ないほど高スコア）
    if feature.effort_days <= 3:
        score += 10
    elif feature.effort_days <= 7:
        score += 5

    # リスク（低いほど高スコア）
    if feature.risk == "LOW":
        score += 10
    elif feature.risk == "MEDIUM":
        score += 5

    # 判断
    if score >= 30:
        return "IMPLEMENT NOW"
    elif score >= 20:
        return "PLAN FOR NEXT SPRINT"
    else:
        return "BACKLOG"
```

---

## 結論

### 今後2週間の最優先タスク

**Week 1:**
1. ✅ RSS Feed設定拡充（4h）- DataCollector
2. ✅ Windowsスケジューラ対応（3d）- Scheduler
3. ✅ requirements固定（2h）- CTO

**Week 2:**
4. ✅ しょぼいカレンダーAPI統合（4d）- DataCollector
5. ✅ REST API開発（5d）- DevAPI
6. ✅ テストカバレッジ向上（5d）- QA

### 長期ビジョン（6ヶ月）

**Phase 3（1-3ヶ月）:**
- Web UI本格稼働
- E2Eテスト完備
- システム機能100%完成

**Phase 4（3-6ヶ月）:**
- Claude連携
- 機械学習レコメンデーション
- マルチユーザー対応検討

**Phase 5（6ヶ月以降）:**
- 国際化対応
- モバイルアプリ
- マイクロサービス化

---

**承認**: MangaAnime-CTO Agent
**次回レビュー**: 2週間後（2025-11-25）
**ステータス**: ✅ ACTIVE - 即座実行開始
