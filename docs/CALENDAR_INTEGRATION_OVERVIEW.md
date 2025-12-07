# Googleカレンダー統合実装概要書

**作成日**: 2025-12-07
**対象プロジェクト**: MangaAnime-Info-delivery-system
**バージョン**: 1.0.0
**ステータス**: 設計フェーズ完了→実装準備中

---

## 1. はじめに

本ドキュメントは、アニメ・マンガの最新リリース情報をGoogleカレンダーに自動登録する機能の統合実装について、全体像をまとめたものです。

### 1.1 対象読者
- プロジェクトマネージャー
- バックエンド開発リード
- データベースエンジニア
- QA/テストマネージャー

---

## 2. 全体システムアーキテクチャ

### 2.1 処理フロー（概略図）

```
┌─────────────────────────────────────────────────┐
│          定期実行 (毎朝 08:00 via cron)          │
│       release_notifier.py がトリガー             │
└────────────┬──────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│   ステップ 1: 未同期リリースの抽出               │
│   SELECT * FROM releases                       │
│   WHERE calendar_synced = 0                    │
│   AND release_date >= TODAY                    │
│   AND release_date <= TODAY + 30days           │
└────────────┬──────────────────────────────────┘
             │ (例: 50件のリリース)
             │
             ▼
┌─────────────────────────────────────────────────┐
│   ステップ 2: フィルタリング                     │
│   ├─ NGキーワード確認                           │
│   ├─ ユーザー設定フィルタ適用                   │
│   └─ 既に登録済みの確認                        │
└────────────┬──────────────────────────────────┘
             │ (フィルタ後: 40件)
             │
             ▼
┌─────────────────────────────────────────────────┐
│   ステップ 3: イベント情報の構築                 │
│   ├─ タイトル生成                              │
│   │  例: "約束のネバーランド 第3話配信"         │
│   ├─ 説明文の作成                              │
│   ├─ リマインダー設定                          │
│   └─ 色分け（アニメ=青、マンガ=緑）            │
└────────────┬──────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│   ステップ 4: Google Calendar API 呼び出し      │
│   ├─ OAuth2認証                                │
│   ├─ events().insert() / update()              │
│   └─ エラー時はリトライ（最大3回）             │
└────────────┬──────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼ Success     ▼ Error
    ┌────────┐  ┌─────────────┐
    │  DB更新 │  │エラー記録   │
    └────┬───┘  │リトライ予定 │
         │      └─────────────┘
         ▼
    releases テーブル
    ├─ calendar_synced = 1
    ├─ calendar_event_id = "event123..."
    └─ calendar_synced_at = NOW()

    calendar_sync_log テーブル
    ├─ sync_status = 'synced'
    ├─ google_event_id = "event123..."
    └─ synced_at = NOW()
```

### 2.2 システム全体図

```
┌─────────────────────────────────────────────────────────┐
│                     既存システム                         │
│  ┌─────────────┐     ┌──────────┐     ┌────────────┐  │
│  │ AniList API │     │RSS Parser│     │ DB (SQLite)│  │
│  └──────┬──────┘     └────┬─────┘     └──────┬─────┘  │
│         │                 │                   │        │
│         └─────────────────┼───────────────────┘        │
│                           ▼                            │
│              ┌─────────────────────────┐               │
│              │  release_notifier.py    │               │
│              │  (Gmail通知を実行)       │               │
│              └───────────┬─────────────┘               │
└──────────────────────────┼──────────────────────────────┘
                           │
                    ┌──────▼────────┐
                    │新機能: カレンダー│
                    │     統合        │
                    └──────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐        ┌──────────┐      ┌─────────┐
    │ DB拡張 │        │API ラッパー│    │同期ロジック│
    │テーブル│        │(Google)   │    │マネージャー│
    └────────┘        └──────────┘      └─────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │Google Calendar│
                    │     API      │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ユーザーの      │
                    │Googleカレンダー│
                    └──────────────┘
```

---

## 3. 実装成果物一覧

### 3.1 データベース関連

| ファイル | 内容 | ステータス |
|---------|------|----------|
| `migrations/006_add_calendar_sync.sql` | マイグレーション本体 | 設計完了 |
| `migrations/rollback/006_rollback.sql` | ロールバック処理 | 設計完了 |

### 3.2 実装コード（スケルトン）

| ファイル | 内容 | 予定行数 |
|---------|------|--------|
| `scripts/sync_calendar.py` | メインスクリプト | 200-250行 |
| `scripts/modules/calendar_api.py` | Google Calendar APIラッパー | 300-400行 |
| `scripts/modules/calendar_sync_manager.py` | 同期ロジック管理 | 400-500行 |
| `scripts/modules/calendar_event_builder.py` | イベント構築ユーティリティ | 150-200行 |

### 3.3 ドキュメント

| ファイル | 内容 | 状態 |
|---------|------|------|
| `docs/CALENDAR_SYNC_DESIGN.md` | 設計書（詳細） | 完了 |
| `docs/CALENDAR_SCHEMA_REFERENCE.md` | スキーマリファレンス | 完了 |
| `docs/CALENDAR_INTEGRATION_ESTIMATION.md` | 工数見積書 | 完了 |
| `docs/CALENDAR_INTEGRATION_OVERVIEW.md` | このファイル | 完了 |

### 3.4 テスト関連

| ファイル | 内容 | 予定テストケース |
|---------|------|-----------------|
| `tests/test_calendar_api.py` | API ラッパーテスト | 20-30 |
| `tests/test_calendar_sync_manager.py` | 同期マネージャーテスト | 25-35 |
| `tests/test_sync_calendar.py` | エンド・ツー・エンドテスト | 15-20 |
| `tests/fixtures/calendar_test_data.py` | テストデータ | - |

---

## 4. 主要な設計判断

### 4.1 データベーススキーマ設計

#### なぜこの設計か？

```
決定 1: releases テーブルへのカラム追加
┌─────────────────────────────────────────┐
│ 他の選択肢:                             │
│ - 別テーブル google_events               │
│   (外部キーで releases と紐付け)         │
│                                         │
│ 採用理由:                               │
│ + releases と一対一の関係                │
│ + クエリが単純で高速                     │
│ + NULL許可でオプション性を確保           │
│ - 構造は若干複雑になる（但し許容範囲）   │
└─────────────────────────────────────────┘

決定 2: calendar_sync_log テーブルの作成
┌─────────────────────────────────────────┐
│ 他の選択肢:                             │
│ - 同期ログなし（メモリに保持）           │
│                                         │
│ 採用理由:                               │
│ + 完全な監査証跡が必要                   │
│ + エラーハンドリング・リトライが必須     │
│ + 今後の分析・改善に必要                │
└─────────────────────────────────────────┘

決定 3: calendar_metadata テーブルの作成
┌─────────────────────────────────────────┐
│ 他の選択肢:                             │
│ - メタデータを releases に統合            │
│                                         │
│ 採用理由:                               │
│ + 将来のカスタマイズに対応               │
│ + ユーザー設定の保存に対応               │
│ + 正規化による整合性確保                │
└─────────────────────────────────────────┘
```

### 4.2 API設計パターン

#### 非同期 vs 同期処理

```
採用: 同期処理（当初実装）
理由:
  + 実装がシンプル
  + デバッグが容易
  + 定期実行のため性能非課題

注: 1000件超える場合は
    非同期キューの導入を検討
```

#### エラーハンドリング

```
採用: 指数バックオフ + リトライ（最大3回）
理由:
  + 一時的なネットワークエラーに強い
  + Google API レート制限に対応
  + リトライ回数限定で無限ループ防止

リトライ間隔:
  1回目: 1分
  2回目: 5分
  3回目: 15分
  （以降はスキップ、ログ記録）
```

---

## 5. 統合ポイント

### 5.1 既存システムとの連携

#### release_notifier.py への追加

```python
# release_notifier.py
def main():
    # ... 既存処理 ...

    # Gmail通知実行
    send_notification(releases)

    # 【新機能】カレンダー同期実行
    from scripts.sync_calendar import sync_calendar_events
    sync_calendar_events()  # 追加

    logging.info("All tasks completed")

if __name__ == '__main__':
    main()
```

#### config.json への設定追加

```json
{
  "google": {
    "calendar": {
      "sync_enabled": true,
      "sync_days_ahead": 30,
      "batch_size": 50,
      "max_retries": 3,
      "reminder_minutes": 1440
    }
  }
}
```

### 5.2 データベース連携

#### 新しいDB メソッド一覧

```python
# DB メソッド（modules/db.py に追加）

# 1. 未同期リリース取得
def get_unsynced_releases(days_ahead=30):
    """未同期かつ30日以内のリリース取得"""

# 2. releases テーブル更新
def update_release_calendar_sync(release_id, **kwargs):
    """calendar_synced, calendar_event_id, calendar_synced_at 更新"""

# 3. メタデータ取得・作成
def get_calendar_metadata(release_id):
    """カレンダーメタデータ取得"""

def create_calendar_metadata(release_id, metadata_dict):
    """新しいメタデータ作成"""

# 4. 同期ログ操作
def log_calendar_sync(release_id, work_id, **sync_info):
    """同期ログ記録"""

def get_calendar_sync_log(release_id):
    """同期ログ取得"""

# 5. 統計情報
def get_sync_statistics(start_date, end_date):
    """期間内の同期統計取得"""
```

---

## 6. 運用シナリオ

### 6.1 通常オペレーション

```
毎日 08:00
  ↓
cron が release_notifier.py 実行
  ↓
sync_calendar_events() 実行
  ↓
1. 未同期リリース 50件を取得
2. Google Calendar API で 50個のイベント作成
3. DB テーブル更新
4. ログ記録
  ↓
【完了】
  ↓
17:00 に自動スケジューラが本番環境ヘルスチェック
```

### 6.2 エラーシナリオ

#### シナリオ 1: API 429エラー（レート制限）

```
発生: バッチサイズが大きすぎて API レート制限に達した
対応:
  1. エラーをキャッチ → calendar_sync_log に記録
  2. リトライ待機（指数バックオフ）
  3. 次回実行時に自動リトライ
  4. 3回失敗後は手動対応（アラート通知）
```

#### シナリオ 2: DB 接続エラー

```
発生: DB サーバーがダウン
対応:
  1. 例外をキャッチ
  2. ログに記録
  3. メール通知（DevOps チーム）
  4. 手動リカバリ
```

#### シナリオ 3: OAuth2 認証失敗

```
発生: token.json が無効 / 期限切れ
対応:
  1. リトライして再度取得
  2. 失敗が続く場合は アラート
  3. 手動で credentials を更新
  4. 次回実行で自動継続
```

---

## 7. 本番環境準備チェックリスト

### Pre-Deployment

- [ ] Google Cloud Project の準備
  - [ ] Calendar API 有効化
  - [ ] OAuth2 認証情報ダウンロード
  - [ ] テストユーザーアカウント設定

- [ ] ステージング環境検証
  - [ ] マイグレーション 006 実行確認
  - [ ] 全テストケース合格
  - [ ] パフォーマンステスト完了
  - [ ] UAT 承認取得

- [ ] ドキュメント完備
  - [ ] 運用マニュアル完成
  - [ ] トラブルシューティングガイド完成
  - [ ] チーム教育実施

### Deployment Day

- [ ] 本番環境 DB バックアップ取得
- [ ] マイグレーション 006 実行
- [ ] スクリプト配置 (/usr/local/bin など)
- [ ] 権限設定 (chmod 755)
- [ ] Cron エントリ追加
- [ ] 初回実行テスト
- [ ] Google Calendar で確認
- [ ] ログファイル確認

### Post-Deployment

- [ ] 3日間の監視（毎日09:00確認）
- [ ] エラーログ確認
- [ ] Google Calendar イベント確認
- [ ] メトリクス収集
- [ ] チーム間の知識共有
- [ ] 定期監視スケジュール確定

---

## 8. パフォーマンス目標と実現手法

### 目標

| 指標 | 目標値 | 実現手法 |
|------|--------|--------|
| 単件同期時間 | < 2秒 | API 最適化、キャッシング |
| 100件同期 | < 3分 | バッチ処理、非同期呼び出し検討 |
| 1000件同期 | < 30分 | ページネーション、キュー導入 |
| API 成功率 | > 99% | リトライ、エラーハンドリング |
| メモリ使用量 | < 100MB | ストリーミング処理 |

### 最適化戦略

```python
# 1. バッチ処理
BATCH_SIZE = 50

for i in range(0, len(releases), BATCH_SIZE):
    batch = releases[i:i+BATCH_SIZE]
    for release in batch:
        sync_release(release)

# 2. キャッシング
work_cache = {}
for release in releases:
    if release['work_id'] not in work_cache:
        work_cache[release['work_id']] = get_work(...)

# 3. 接続プーリング
# DB: SQLite 3は単一接続で十分
# API: requests Session を使用して接続再利用
```

---

## 9. セキュリティ考慮事項

### 認証情報管理

```
OAuth2 Token 保存位置:
  - 本番: /secure/path/credentials/token.json (root のみ読取)
  - ステージング: ~/.config/google/token.json

環境変数化:
  GOOGLE_CALENDAR_CREDENTIALS_PATH=/secure/path/token.json
  GOOGLE_CALENDAR_ID=primary
```

### データセキュリティ

```
転送:
  - Google API: HTTPS のみ（自動）
  - DB通信: ローカルのみ

保存:
  - イベントIDはデータベースに保存（復号化不要）
  - 個人情報（ユーザーメール）は保存しない
```

---

## 10. 監視・アラート

### 監視ポイント

```yaml
メトリクス:
  - 日次同期リリース数
  - エラー発生率
  - 平均同期時間
  - API レート使用率

ログ監視:
  - ERROR レベルのログ検出
  - CRITICAL: API 認証エラー
  - WARNING: リトライ発生

アラート設定:
  - エラー率 > 5% → Slack 通知
  - 同期成功率 < 90% → メール通知
  - API 呼び出し失敗 → PagerDuty
```

---

## 11. ロードマップ（将来の拡張）

### Phase 2 (Q1 2026)
- [ ] 非同期キューの導入（Celery/RQ）
- [ ] 複数カレンダーサポート
- [ ] ユーザーごとのカレンダー管理
- [ ] Web UI での設定管理

### Phase 3 (Q2 2026)
- [ ] AI による最適なリマインダー提案
- [ ] スマートフィルタリング
- [ ] カレンダーとGmail の完全統合
- [ ] Googleスプレッドシート エクスポート

### Phase 4 (Q3 2026)
- [ ] Apple Calendar / Outlook 対応
- [ ] JSON API 公開
- [ ] Webhook サポート

---

## 12. よくある質問（FAQ）

### Q1: なぜ別テーブルではなく releases テーブルへ直接カラムを追加するのか？

**A**: releases とカレンダーイベントは一対一の関係です。別テーブルにするとジョインが増えて複雑になり、メンテナンスが難しくなります。

### Q2: エラー発生時の対応はどうなるのか？

**A**: calendar_sync_log テーブルに記録され、最大3回まで自動リトライされます。3回失敗すると sync_status = 'failed' となり、管理者がダッシュボードで確認できます。

### Q3: 既に登録されたイベントを更新したい場合は？

**A**: calendar_event_id が既に設定されている releases では update イベント処理が走ります。Google Calendar API は idempotent なので、何度実行しても安全です。

### Q4: 大量の過去リリースを同期したい場合は？

**A**: `get_unsynced_releases()` で日数を拡張するか、直接 SQL でクエリ条件を変更してください。バッチサイズ最適化も検討をお勧めします。

### Q5: テスト時に実際の Google Calendar を污さないようにするには？

**A**: テスト用 Google アカウントと `calendar_id` を指定してください。さらに calendar_metadata テーブルで calendar_id を 'test' に設定すれば、テスト専用カレンダーへの登録が可能です。

---

## 13. まとめ

このGoogleカレンダー統合実装により、以下を実現できます:

✅ **自動化**: リリース情報を自動でカレンダーに登録
✅ **信頼性**: エラーハンドリングとリトライ機構
✅ **監査性**: 完全なログ記録と状態追跡
✅ **拡張性**: メタデータテーブルによるカスタマイズ対応
✅ **運用性**: clear なドキュメントとチェックリスト

**次のステップ**: 本ドキュメントが承認されたら、即座に開発フェーズに移行できます。

---

## 付録：ファイル一覧

```
MangaAnime-Info-delivery-system/
├── migrations/
│   ├── 006_add_calendar_sync.sql          ← 設計完了
│   └── rollback/
│       └── 006_rollback.sql               ← 設計完了
│
├── scripts/
│   ├── sync_calendar.py                   ← 実装予定
│   └── modules/
│       ├── calendar_api.py                ← 実装予定
│       └── calendar_sync_manager.py       ← 実装予定
│
├── tests/
│   ├── test_calendar_api.py               ← 実装予定
│   ├── test_calendar_sync_manager.py      ← 実装予定
│   └── test_sync_calendar.py              ← 実装予定
│
└── docs/
    ├── CALENDAR_SYNC_DESIGN.md            ← 設計書 完了
    ├── CALENDAR_SCHEMA_REFERENCE.md       ← スキーマリファレンス 完了
    ├── CALENDAR_INTEGRATION_ESTIMATION.md ← 工数見積 完了
    └── CALENDAR_INTEGRATION_OVERVIEW.md   ← このファイル 完了
```

---

**作成**: データベース設計エージェント
**レビュー**: テックリード（承認待機）
**承認日**: TBD
