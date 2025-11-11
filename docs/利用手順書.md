# MangaAnime情報配信システム - 利用手順書

## 📚 目次

1. [システム要件](#システム要件)
2. [初回セットアップ](#初回セットアップ)
3. [Google API設定](#google-api設定)
4. [システム実行](#システム実行)
5. [自動化設定](#自動化設定)
6. [設定カスタマイズ](#設定カスタマイズ)

## システム要件

### 動作環境
- **OS**: Linux (Ubuntu 20.04以上推奨)
- **Python**: 3.12以上
- **メモリ**: 最低512MB
- **ストレージ**: 最低1GB空き容量
- **ネットワーク**: インターネット接続必須

### 前提条件
- Googleアカウント（Gmail、Calendar使用）
- 基本的なコマンドライン操作知識
- テキストエディタの使用経験

## 初回セットアップ

### 1. プロジェクトファイルの確認

```bash
cd /path/to/MangaAnime-Info-delivery-system
ls -la
```

以下のファイルが存在することを確認：
- `release_notifier.py` (メインスクリプト)
- `config.json` (設定ファイル)
- `requirements.txt` (依存関係)
- `modules/` ディレクトリ

### 2. Python仮想環境の作成

```bash
# 仮想環境作成
python3 -m venv venv

# 仮想環境有効化
source venv/bin/activate

# 依存ライブラリインストール
pip install -r requirements.txt
```

### 3. 設定ファイルの編集

`config.json`を開いて、Gmail設定を更新：

```json
{
  "google": {
    "gmail": {
      "from_email": "your-email@gmail.com",
      "to_email": "your-email@gmail.com"
    }
  }
}
```

## Google API設定

### 1. Google Cloud Console設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. **APIとサービス** → **ライブラリ**から以下を有効化：
   - Gmail API
   - Google Calendar API

### 2. OAuth同意画面の設定

1. **APIとサービス** → **OAuth同意画面**
2. **アプリ情報**を設定：
   - アプリ名: `MangaAnime情報配信システム`
   - ユーザーサポートメール: あなたのGmail
   - デベロッパー連絡先: あなたのGmail

### 3. 認証情報の作成

1. **APIとサービス** → **認証情報**
2. **認証情報を作成** → **OAuth クライアントID**
3. **アプリケーションの種類**: デスクトップアプリケーション
4. 作成後、JSONファイルをダウンロード
5. ファイル名を`credentials.json`に変更してプロジェクトルートに配置

### 4. 認証トークンの生成

```bash
# 認証URL生成
python3 create_token_simple.py
```

表示されたURLをブラウザで開いて認証後、以下を実行：

```bash
# 認証コードを使用してトークン作成
python3 generate_token.py
```

## システム実行

### 1. テスト実行

```bash
# ドライラン（通知なし）
python3 release_notifier.py --dry-run

# 詳細ログ付きテスト
python3 release_notifier.py --dry-run --verbose
```

### 2. 通知機能テスト

```bash
# Gmail/Calendar統合テスト
python3 test_notification.py
```

成功メッセージを確認：
- ✅ Gmail認証成功
- ✅ テストメール送信成功
- ✅ Googleカレンダー認証成功
- ✅ テストカレンダーイベント作成成功

### 3. 本番実行

```bash
# 通常実行（実際に通知送信）
python3 release_notifier.py
```

## 自動化設定

### 1. cron設定

```bash
# crontab編集
crontab -e

# 以下を追加（毎朝8:00に実行）
0 8 * * * cd /path/to/MangaAnime-Info-delivery-system && source venv/bin/activate && python3 release_notifier.py >> logs/cron.log 2>&1
```

### 2. ログローテーション設定

`/etc/logrotate.d/manga-anime-notifier`を作成：

```
./logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

## 設定カスタマイズ

### 1. フィルタリング設定

`config.json`でNGキーワードをカスタマイズ：

```json
{
  "filtering": {
    "ng_keywords": [
      "エロ", "R18", "成人向け", "BL", "百合"
    ],
    "ng_genres": ["Hentai", "Ecchi"],
    "exclude_tags": ["Adult Cast", "Erotica"]
  }
}
```

### 2. 通知設定

```json
{
  "notification": {
    "email": {
      "enabled": true,
      "max_items_per_email": 20,
      "include_images": true
    },
    "calendar": {
      "enabled": true,
      "create_all_day_events": false
    }
  }
}
```

### 3. 実行スケジュール設定

```json
{
  "scheduling": {
    "default_run_time": "08:00",
    "timezone": "Asia/Tokyo",
    "retry_attempts": 3
  }
}
```

### 4. RSS フィード追加

新しいRSSフィードを追加する場合：

```json
{
  "apis": {
    "rss_feeds": {
      "feeds": [
        {
          "name": "新しいフィード名",
          "url": "https://example.com/rss",
          "category": "manga",
          "enabled": true
        }
      ]
    }
  }
}
```

## 📊 実行結果の確認

### ログファイル確認

```bash
# 最新のログ確認
tail -f logs/app.log

# エラーログの検索
grep "ERROR" logs/app.log

# 通知成功の確認
grep "Email sent successfully" logs/app.log
```

### データベース確認

```bash
# SQLiteでデータベース確認
sqlite3 db.sqlite3

# テーブル確認
.tables

# データ確認
SELECT * FROM releases WHERE notified = 0 LIMIT 5;
.quit
```

## 🔧 基本的なトラブルシューティング

### 認証エラーの場合

```bash
# トークンファイル削除
rm token.json

# 再認証
python3 create_token_simple.py
```

### 依存ライブラリエラーの場合

```bash
# 仮想環境再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### データベースエラーの場合

```bash
# データベース再初期化
rm db.sqlite3
python3 release_notifier.py --dry-run
```

---

**重要**: 本番運用前に必ずテスト実行で動作確認を行ってください。

**サポート**: トラブル発生時は`logs/app.log`を確認し、エラーメッセージを参照してください。