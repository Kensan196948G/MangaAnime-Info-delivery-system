# Googleカレンダー機能 セットアップサマリー

**作成日**: 2025-12-06
**作成者**: Backend Developer Agent
**プロジェクト**: MangaAnime-Info-delivery-system

---

## 作成ファイル一覧

このタスクで以下のファイルを作成しました:

### 1. ドキュメント

| ファイル名 | 説明 | パス |
|----------|------|------|
| **CALENDAR_INVESTIGATION_REPORT.md** | 詳細調査・分析レポート | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/` |
| **CALENDAR_QUICKSTART.md** | クイックスタートガイド（5分で開始） | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/` |
| **CALENDAR_SETUP_SUMMARY.md** | このファイル（サマリー） | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/` |

### 2. 実装ファイル

| ファイル名 | 説明 | パス |
|----------|------|------|
| **modules/calendar_template.py** | Googleカレンダー連携モジュール実装 | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules/` |

**主な機能:**
- OAuth2認証
- イベント作成・更新・削除
- イベント一覧取得
- エラーハンドリング
- ログ記録

### 3. テストスクリプト

| ファイル名 | 説明 | パス |
|----------|------|------|
| **test_calendar_dry_run.py** | Dry-runテスト（APIを呼ばない） | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/` |

**機能:**
- 環境チェック
- 設定ファイル確認
- テストデータ生成
- JSON形式での出力確認

### 4. セットアップスクリプト

| ファイル名 | 説明 | パス |
|----------|------|------|
| **setup_google_calendar.sh** | 自動セットアップスクリプト | `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/` |

**機能:**
- 必要パッケージの自動インストール
- 認証ファイルの確認
- パーミッション設定
- 認証テストの実行

---

## クイックスタート

### 最速セットアップ（5分）

```bash
# 1. プロジェクトに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 2. セットアップスクリプト実行
bash setup_google_calendar.sh

# 3. Dry-runテスト
python3 test_calendar_dry_run.py
```

### credentials.json取得が必要な場合

1. https://console.cloud.google.com/
2. プロジェクト作成 → Calendar API有効化
3. OAuth 2.0認証情報作成（デスクトップアプリ）
4. credentials.jsonダウンロード
5. プロジェクトルートに配置

**詳細**: `CALENDAR_QUICKSTART.md` 参照

---

## 実装状況

### 完了項目

- [x] カレンダーモジュール設計・実装
- [x] OAuth2認証フロー実装
- [x] イベント作成機能
- [x] イベント更新機能
- [x] イベント削除機能
- [x] イベント一覧取得機能
- [x] エラーハンドリング
- [x] ログ記録
- [x] 設定ファイル対応
- [x] Dry-runテスト実装
- [x] セットアップスクリプト作成
- [x] ドキュメント作成

### 未実装項目（今後の拡張）

- [ ] 重複防止機能（DB連携）
- [ ] バッチイベント作成
- [ ] イベント色分け自動化
- [ ] リトライ機能（Exponential backoff）
- [ ] 複数カレンダー対応
- [ ] iCal形式エクスポート

---

## ファイル構成図

```
MangaAnime-Info-delivery-system/
│
├── CALENDAR_INVESTIGATION_REPORT.md    # 詳細調査レポート
├── CALENDAR_QUICKSTART.md              # クイックスタートガイド
├── CALENDAR_SETUP_SUMMARY.md           # このファイル
│
├── setup_google_calendar.sh            # セットアップスクリプト
├── test_calendar_dry_run.py            # Dry-runテスト
│
├── modules/
│   └── calendar_template.py            # カレンダーモジュール実装
│
├── credentials.json                    # Google API認証情報（要取得）
├── token.json                          # OAuth2トークン（自動生成）
└── config.json                         # システム設定
```

---

## 使用例

### 例1: アニメ配信通知

```python
from modules.calendar import CalendarManager
from datetime import datetime, timedelta

cal = CalendarManager()
cal.authenticate()

result = cal.create_event(
    title='呪術廻戦 第15話配信 - Netflix',
    description='配信プラットフォーム: Netflix',
    start_datetime=datetime.now() + timedelta(days=1),
    color='9'  # 青（アニメ）
)

print(result)
```

### 例2: マンガ発売通知

```python
result = cal.create_event(
    title='ワンピース 第110巻発売',
    description='電子版配信',
    start_datetime=datetime(2025, 12, 15, 0, 0, 0),
    color='10'  # 緑（マンガ）
)

print(result)
```

---

## テスト方法

### テスト1: 環境確認

```bash
python3 test_calendar_dry_run.py
```

**確認項目:**
- Pythonバージョン
- 必要パッケージインストール状況
- 認証ファイル存在確認
- 設定ファイル確認

---

### テスト2: 認証テスト

```bash
python3 modules/calendar.py --authenticate
```

**期待される動作:**
1. ブラウザが開く
2. Googleアカウントでログイン
3. アプリケーション許可
4. token.json自動生成

---

### テスト3: イベント作成テスト

```bash
python3 modules/calendar.py --create-test-event
```

**確認:**
- Googleカレンダーに「[テスト] カレンダー連携テスト」が作成される
- 開始日時: 明日12:00

---

## トラブルシューティング

### よくあるエラー

| エラー | 原因 | 解決策 |
|-------|------|--------|
| `ModuleNotFoundError: No module named 'google'` | Google APIライブラリ未インストール | `pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client` |
| `credentials.json not found` | 認証ファイル未配置 | Google Cloud Consoleから取得して配置 |
| `token.json has expired` | トークン期限切れ | `rm token.json` して再認証 |
| `Calendar API has not been used` | API未有効化 | Google Cloud ConsoleでCalendar API有効化 |

詳細: `CALENDAR_QUICKSTART.md` のトラブルシューティングセクション参照

---

## セキュリティ注意事項

### 認証ファイルの取り扱い

**重要**: 以下のファイルは絶対に公開リポジトリにコミットしないこと

- `credentials.json` - Google API認証情報
- `token.json` - OAuth2アクセストークン

### .gitignore設定

```gitignore
# Google API認証ファイル
credentials.json
token.json

# テストレポート
test_calendar_dry_run_report.json
```

### パーミッション設定

```bash
chmod 600 credentials.json
chmod 600 token.json
```

---

## API制限

### Google Calendar API無料枠

- **クエリ数**: 1,000,000クエリ/日
- **レート制限**: 通常使用では問題なし

### 推奨事項

- バッチ処理時はイベントをまとめて作成
- 不要なイベント一覧取得を避ける
- エラー時はリトライ前に待機時間を設ける

---

## 次のステップ

### 優先度: 高

1. **credentials.json取得**
   - Google Cloud Console設定
   - Calendar API有効化
   - OAuth 2.0認証情報作成

2. **初回認証実行**
   - `setup_google_calendar.sh` 実行
   - ブラウザでログイン
   - token.json生成確認

3. **動作確認**
   - Dry-runテスト成功
   - テストイベント作成
   - Googleカレンダーで確認

### 優先度: 中

1. **modules/calendar.pyへのリネーム**
   ```bash
   mv modules/calendar_template.py modules/calendar.py
   ```

2. **config.jsonへの設定追加**
   - Google Calendar設定セクション追加
   - 色分け設定
   - リマインダー設定

3. **既存システムとの統合**
   - release_notifier.pyからの呼び出し
   - DBとの連携（重複防止）

### 優先度: 低

1. **拡張機能実装**
   - イベント色分け自動化
   - バッチ作成機能
   - リトライ機能

2. **Web UI統合**
   - カレンダー設定画面
   - イベント一覧表示

---

## 参考資料

### 作成ドキュメント

1. **CALENDAR_INVESTIGATION_REPORT.md**
   - 詳細な調査結果
   - 実装仕様
   - 認証手順書
   - テスト計画

2. **CALENDAR_QUICKSTART.md**
   - 5分で始めるガイド
   - ステップバイステップ手順
   - トラブルシューティング
   - 使用例

### 外部リンク

- [Google Calendar API公式](https://developers.google.com/calendar/api/v3/reference)
- [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- [OAuth 2.0認証](https://developers.google.com/identity/protocols/oauth2)

---

## 質問・サポート

### よくある質問

**Q: credentials.jsonはどこで取得できますか？**
A: Google Cloud Console（https://console.cloud.google.com/）で取得できます。詳細は`CALENDAR_QUICKSTART.md`のステップ2参照。

**Q: 初回認証でブラウザが開きません**
A: ターミナルに表示されるURLを手動でブラウザにコピー＆ペーストしてください。

**Q: イベントが作成されません**
A: `test_calendar_dry_run.py`で環境チェックを実行し、全ての項目が✓になっているか確認してください。

**Q: token.jsonは削除しても大丈夫ですか？**
A: 大丈夫です。削除後、再度`--authenticate`で認証すれば再生成されます。

---

## まとめ

### 作成した成果物

- **ドキュメント**: 3ファイル（詳細レポート、クイックスタート、サマリー）
- **実装**: 1ファイル（カレンダーモジュール）
- **テスト**: 1ファイル（Dry-runテスト）
- **スクリプト**: 1ファイル（自動セットアップ）

### 実装状況

- **カレンダー機能**: 完全実装済み
- **認証フロー**: 実装済み
- **テスト**: Dry-runテスト実装済み
- **ドキュメント**: 完備

### 次のアクション

1. `bash setup_google_calendar.sh` 実行
2. Google Cloud Console設定
3. 初回認証実行
4. テストイベント作成
5. 既存システムと統合

---

**セットアップ準備完了！**

詳細な手順は各ドキュメントを参照してください。

- クイックスタート: `CALENDAR_QUICKSTART.md`
- 詳細調査: `CALENDAR_INVESTIGATION_REPORT.md`
