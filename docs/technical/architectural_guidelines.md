# アニメ・マンガ情報配信システム - アーキテクチャガイドライン

## 1. システム設計方針

### 1.1 アーキテクチャ原則
- **モジュラリティ**: 各機能は独立したモジュールとして実装
- **設定駆動**: すべての動作は config.json で制御可能
- **エラーハンドリング**: 堅牢なエラー処理と詳細ログ出力
- **拡張性**: 新しいデータソースや通知方法を容易に追加可能
- **セキュリティ**: OAuth2認証とトークンの安全な管理

### 1.2 技術スタック
```
Frontend: なし（CLIアプリケーション + 管理用WebUI）
Backend: Python 3.8+
Database: SQLite3
APIs: AniList GraphQL、RSS feeds、Gmail API、Google Calendar API
Authentication: OAuth2 (Google)
Scheduling: cron (Linux)
```

## 2. ディレクトリ構成

```
./
├── config.json                 # メイン設定ファイル
├── config.json.template         # 設定テンプレート
├── release_notifier.py          # メインエントリポイント
├── requirements.txt             # 本番依存関係
├── requirements-dev.txt         # 開発依存関係
├── db.sqlite3                   # SQLiteデータベース
├── credentials.json             # Google API認証情報
├── token.json                   # OAuth2トークン（自動生成）
├── logs/                        # ログファイル
│   ├── app.log
│   └── app.json
├── modules/                     # 各機能モジュール
│   ├── __init__.py
│   ├── config.py                # 設定管理
│   ├── db.py                    # データベース操作
│   ├── logger.py                # ログ設定
│   ├── anime_anilist.py         # AniList API連携
│   ├── manga_rss.py             # RSS フィード処理
│   ├── filter_logic.py          # コンテンツフィルタリング
│   ├── mailer.py                # Gmail通知
│   ├── calendar.py              # Googleカレンダー連携
│   └── monitoring.py            # システム監視
├── tests/                       # テストコード
├── scripts/                     # 運用スクリプト
└── docs/                        # ドキュメント
```

## 3. モジュール設計原則

### 3.1 依存関係の管理
```python
# 推奨: 遅延インポートで循環参照を回避
def _import_modules(self):
    if self._collectors is None:
        from modules.anime_anilist import AniListCollector
        # ... その他のインポート
```

### 3.2 設定管理
- すべてのモジュールは ConfigManager から設定を取得
- 環境変数による設定上書きをサポート
- 設定変更時はバリデーションを実行

### 3.3 エラーハンドリング
```python
# 推奨パターン
try:
    result = some_operation()
    self.logger.info(f"Operation successful: {result}")
except SpecificException as e:
    self.logger.error(f"Specific error occurred: {e}")
    # 適切な回復処理
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    if self.logger.isEnabledFor(logging.DEBUG):
        self.logger.debug(traceback.format_exc())
    raise
```

## 4. データベース設計

### 4.1 テーブル設計
```sql
-- 作品情報テーブル
CREATE TABLE works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  title_kana TEXT,
  title_en TEXT,
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(title, type)
);

-- リリース情報テーブル  
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
  UNIQUE(work_id, release_type, number, platform, release_date),
  FOREIGN KEY (work_id) REFERENCES works (id)
);
```

### 4.2 データ整合性
- ユニーク制約による重複防止
- 外部キー制約による参照整合性
- トランザクション処理による原子性保証

## 5. API設計ガイドライン

### 5.1 レート制限対応
```python
# 推奨: 設定ベースのレート制限
class AniListCollector:
    def __init__(self, config):
        self.rate_limit = config.get_anilist_config().rate_limit
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        min_interval = 60 / self.rate_limit.requests_per_minute
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
```

### 5.2 タイムアウト処理
- すべてのHTTP要求に適切なタイムアウト設定
- 段階的なリトライ機能
- 失敗時のフォールバック戦略

## 6. セキュリティガイドライン

### 6.1 認証情報の管理
- `credentials.json`: Gitにコミットしない
- `token.json`: 自動生成、適切な権限で保護
- 環境変数での設定上書きをサポート

### 6.2 ログのセキュリティ
- 認証トークンや個人情報をログに出力しない
- デバッグレベルでのみ詳細情報を出力
- ログファイルの適切なローテーション

## 7. パフォーマンスガイドライン

### 7.1 データベース最適化
- 適切なインデックスの設定
- バッチ処理による効率化
- 古いデータの定期的なクリーンアップ

### 7.2 メモリ管理
- 大量データ処理時のストリーミング処理
- 不要なオブジェクトの適切な解放
- コネクションプールの活用

## 8. テスト戦略

### 8.1 テストの分類
- **単体テスト**: 各モジュールの機能テスト
- **統合テスト**: API連携テスト
- **E2Eテスト**: システム全体の動作テスト

### 8.2 テストデータ
- モックデータの使用
- テスト環境での実際のAPI呼び出し
- データベースのテストフィクスチャ

## 9. 運用ガイドライン

### 9.1 ログ監視
```bash
# 推奨: ログ監視コマンド
tail -f logs/app.log | grep -E "(ERROR|WARNING)"
```

### 9.2 cron設定例
```bash
# 毎朝8時に実行
0 8 * * * python3 release_notifier.py

# ログローテーション（週次）
0 2 * * 0 find /path/to/logs -name "*.log" -mtime +7 -delete
```

### 9.3 バックアップ戦略
- データベースの日次バックアップ
- 設定ファイルのバックアップ
- ログファイルの保持期間設定

## 10. 開発ワークフロー

### 10.1 Git フロー
- main: 本番環境用
- develop: 開発統合用
- feature/*: 機能開発用

### 10.2 コード品質
- Python PEP 8 準拠
- 型ヒントの使用推奨
- docstring の記述必須

### 10.3 リリース手順
1. 機能テストの完了
2. 統合テストの実行
3. 設定ファイルの検証
4. 本番環境へのデプロイ
5. 監視・ログ確認

---

このアーキテクチャガイドラインに従って開発を進めることで、保守性・拡張性・信頼性の高いシステムを構築できます。