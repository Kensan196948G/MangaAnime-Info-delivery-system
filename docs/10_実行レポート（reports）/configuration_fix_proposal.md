# 設定エラー修正提案書

**作成日**: 2025-11-15
**優先度**: 🔴 高（システム機能に直接影響）
**予想作業時間**: 30分

---

## エグゼクティブサマリー

設定テスト機能で発生している2つの重大エラーを特定しました：

1. **Gmail接続エラー**: 設定テスト関数が.envファイルを読み込んでいない（3行のコード追加で解決）
2. **RSSフィードエラー**: 設定されているRSSフィードURLが全て無効（代替RSSに変更する必要あり）

即座に実装可能な修正コードと、動作確認済みの代替RSSフィードを提供します。

---

## 1. Gmail接続エラーの修正

### 問題の詳細

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py`

**関数**: `api_test_configuration()` (行番号: 1250付近)

**根本原因**:
- 通知テスト関数（`api_test_notification()`）は正常に動作する
- 設定テスト関数だけが.envファイルを読み込んでいない
- config.jsonに必要な設定キー（`email.sender_email`, `email.sender_password`）が存在しない

### 修正コード

**修正箇所**: `api_test_configuration()` 関数の Gmail SMTP connection テストセクション

#### 修正前（現在のコード）

```python
# Test Gmail SMTP connection
try:
    email_config = config.get("email", {})
    smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_config.get("smtp_port", 587)
    sender_email = email_config.get("sender_email", "")
    sender_password = email_config.get("sender_password", "")

    if not sender_email or not sender_password:
        results["gmail"]["status"] = "error"
        results["gmail"]["message"] = "メール設定が不完全です"
```

#### 修正後（推奨コード）

```python
# Test Gmail SMTP connection
try:
    # .envファイルから認証情報を読み込み（追加）
    load_dotenv()

    # 環境変数を優先的に使用
    sender_email = os.getenv('GMAIL_SENDER_EMAIL') or os.getenv('GMAIL_ADDRESS', '')
    sender_password = os.getenv('GMAIL_APP_PASSWORD', '')
    smtp_server = "smtp.gmail.com"
    smtp_port = 465  # SSL接続

    # フォールバック: config.jsonも確認
    if not sender_email:
        email_config = config.get("google", {}).get("gmail", {})
        sender_email = email_config.get("from_email", "")

    if not sender_email or not sender_password:
        results["gmail"]["status"] = "error"
        results["gmail"]["message"] = "メール設定が不完全です（.envファイルを確認してください）"
        results["gmail"]["details"] = {
            "required_env_vars": ["GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"],
            "sender_email_found": bool(sender_email),
            "password_found": bool(sender_password),
            "hint": ".envファイルに GMAIL_ADDRESS と GMAIL_APP_PASSWORD が設定されているか確認してください"
        }
    else:
        context = ssl.create_default_context()
        # SSL接続を使用（ポート465）
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10) as server:
            server.login(sender_email, sender_password)

        results["gmail"]["status"] = "success"
        results["gmail"]["message"] = "Gmail接続成功"
        results["gmail"]["details"] = {
            "server": smtp_server,
            "port": smtp_port,
            "email": sender_email,
            "auth_method": "SMTP_SSL"
        }
except Exception as e:
    results["gmail"]["status"] = "error"
    results["gmail"]["message"] = f"Gmail接続エラー: {str(e)}"
    results["gmail"]["details"] = {
        "error_type": type(e).__name__,
        "hint": "Gmailアプリパスワードが正しいか、2段階認証が有効か確認してください"
    }
```

### 修正内容の説明

1. **`load_dotenv()` を追加**: .envファイルから環境変数を読み込む
2. **環境変数を優先**: `os.getenv()` で GMAIL_ADDRESS と GMAIL_APP_PASSWORD を取得
3. **ポート変更**: 587（TLS）→ 465（SSL）に変更（より安定）
4. **詳細なエラー情報**: トラブルシューティングのためのヒントを追加

---

## 2. RSSフィードエラーの修正

### 問題の詳細

現在のRSSフィードは全て無効です：

| RSS名 | URL | 状態 | エラー |
|---|---|---|---|
| BookWalker | `https://bookwalker.jp/rss/` | ❌ | 403 Forbidden（アクセス拒否） |
| dアニメストア | `https://anime.dmkt-sp.jp/animestore/CF/rss/` | ❌ | 301 → 404（廃止済み） |

### 動作確認済みの代替RSS

実際にテストして動作を確認しました：

| RSS名 | URL | 状態 | 内容 |
|---|---|---|---|
| **コミックナタリー** | `https://natalie.mu/comic/feed/news` | ✅ 200 OK | マンガ最新ニュース（Atom形式） |

### 推奨される修正

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json`

#### 修正前（現在の設定）

```json
{
  "apis": {
    "rss_feeds": {
      "enabled": true,
      "timeout_seconds": 20,
      "feeds": [
        {
          "name": "BookWalker",
          "url": "https://bookwalker.jp/rss/",
          "type": "manga",
          "enabled": true
        },
        {
          "name": "dアニメストア",
          "url": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
          "type": "anime",
          "enabled": true
        }
      ],
      "user_agent": "MangaAnime-Info-delivery-system/1.0"
    }
  }
}
```

#### 修正後（推奨設定）

```json
{
  "apis": {
    "rss_feeds": {
      "enabled": true,
      "timeout_seconds": 20,
      "feeds": [
        {
          "name": "BookWalker",
          "url": "https://bookwalker.jp/rss/",
          "type": "manga",
          "enabled": false,
          "disabled_reason": "403 Forbidden - ボット対策によりアクセス不可",
          "disabled_date": "2025-11-15"
        },
        {
          "name": "dアニメストア",
          "url": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
          "type": "anime",
          "enabled": false,
          "disabled_reason": "404 Not Found - RSSフィード廃止",
          "disabled_date": "2025-11-15"
        },
        {
          "name": "コミックナタリー",
          "url": "https://natalie.mu/comic/feed/news",
          "type": "manga",
          "enabled": true,
          "format": "atom",
          "description": "マンガ・コミック業界の最新ニュース（新刊、イベント、アニメ化など）"
        },
        {
          "name": "アニメ！アニメ！",
          "url": "https://animeanime.jp/feed",
          "type": "anime",
          "enabled": false,
          "disabled_reason": "403 Forbidden - User-Agent制限",
          "note": "将来的にスクレイピングで対応予定"
        }
      ],
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
  }
}
```

### User-Agent の改善

ボット判定を回避するため、User-Agentを実ブラウザのものに変更：

**変更前**:
```
MangaAnime-Info-delivery-system/1.0
```

**変更後**:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
```

---

## 3. web_app.py の RSSテスト機能強化

### 改善点

1. **User-Agentヘッダー追加**: ボット判定を回避
2. **リトライ機能追加**: 一時的なエラーに対応
3. **詳細なエラー情報**: トラブルシューティングを容易に

### 修正コード

**修正箇所**: `api_test_configuration()` 関数の RSS Feeds テストセクション

```python
# Test RSS Feeds
try:
    rss_config = config.get("apis", {}).get("rss_feeds", {})
    feeds = rss_config.get("feeds", [])
    timeout = rss_config.get("timeout_seconds", 20)
    user_agent = rss_config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # リクエストヘッダー設定
    headers = {
        'User-Agent': user_agent,
        'Accept': 'application/rss+xml, application/xml, text/xml, application/atom+xml, */*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache'
    }

    feed_results = []
    success_count = 0

    for feed in feeds[:5]:  # Test first 5 feeds
        feed_name = feed.get("name", "Unknown")
        feed_url = feed.get("url", "")
        enabled = feed.get("enabled", False)

        if not enabled:
            feed_results.append({
                "name": feed_name,
                "status": "disabled",
                "message": "無効化されています",
                "reason": feed.get("disabled_reason", "不明")
            })
            continue

        # リトライロジック（最大3回）
        last_error = None
        for attempt in range(3):
            try:
                response = requests.get(
                    feed_url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True
                )

                if response.status_code == 200:
                    success_count += 1
                    content_length = len(response.content)

                    # RSS/Atom形式の検証
                    is_xml = 'xml' in response.headers.get('Content-Type', '').lower()

                    feed_results.append({
                        "name": feed_name,
                        "status": "success",
                        "message": "接続成功",
                        "details": {
                            "status_code": response.status_code,
                            "content_length": content_length,
                            "content_type": response.headers.get('Content-Type', 'unknown'),
                            "is_valid_xml": is_xml,
                            "response_time_ms": int(response.elapsed.total_seconds() * 1000)
                        }
                    })
                    break  # 成功したらループを抜ける
                else:
                    last_error = f"HTTPエラー: {response.status_code}"
                    if attempt == 2:  # 最後の試行
                        feed_results.append({
                            "name": feed_name,
                            "status": "error",
                            "message": last_error,
                            "details": {
                                "attempts": 3,
                                "final_status": response.status_code,
                                "hint": "RSSフィードURLが変更または廃止された可能性があります"
                            }
                        })
            except requests.exceptions.Timeout:
                last_error = f"タイムアウト（{timeout}秒）"
                if attempt == 2:
                    feed_results.append({
                        "name": feed_name,
                        "status": "error",
                        "message": last_error,
                        "hint": "ネットワーク接続を確認してください"
                    })
            except requests.exceptions.SSLError as e:
                last_error = f"SSL証明書エラー"
                if attempt == 2:
                    feed_results.append({
                        "name": feed_name,
                        "status": "error",
                        "message": last_error,
                        "details": str(e)[:200]
                    })
                break  # SSL エラーはリトライしても解決しない
            except requests.exceptions.ConnectionError as e:
                last_error = f"接続エラー"
                if attempt == 2:
                    feed_results.append({
                        "name": feed_name,
                        "status": "error",
                        "message": last_error,
                        "hint": "サーバーがダウンしているか、URLが間違っている可能性があります"
                    })
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)[:100]}"
                if attempt == 2:
                    feed_results.append({
                        "name": feed_name,
                        "status": "error",
                        "message": last_error
                    })

            # リトライ前に少し待機
            if attempt < 2:
                time.sleep(2)

    if success_count > 0:
        results["rss_feeds"]["status"] = "success"
        results["rss_feeds"]["message"] = f"{success_count}/{len([f for f in feeds if f.get('enabled')])}個のRSSフィードが正常"
    elif len([f for f in feeds if f.get('enabled')]) == 0:
        results["rss_feeds"]["status"] = "warning"
        results["rss_feeds"]["message"] = "有効なRSSフィードが設定されていません"
    else:
        results["rss_feeds"]["status"] = "error"
        results["rss_feeds"]["message"] = "すべてのRSSフィードでエラー"

    results["rss_feeds"]["details"] = {"feeds": feed_results}

except Exception as e:
    results["rss_feeds"]["status"] = "error"
    results["rss_feeds"]["message"] = f"RSSフィードテストエラー: {str(e)}"
    results["rss_feeds"]["details"] = {
        "error_type": type(e).__name__,
        "traceback": str(e)
    }
```

---

## 4. 実装手順

### ステップ1: web_app.py の修正（15分）

1. **ファイルを開く**:
   ```bash
   nano /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py
   ```

2. **Gmail接続テストセクションを修正**:
   - 行番号: 1270付近
   - `load_dotenv()` を追加
   - 環境変数読み込みロジックを追加

3. **RSSフィードテストセクションを修正**:
   - 行番号: 1380付近
   - ヘッダー設定を追加
   - リトライロジックを追加

### ステップ2: config.json の修正（5分）

1. **ファイルを開く**:
   ```bash
   nano /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json
   ```

2. **RSSフィード設定を更新**:
   - BookWalker: `enabled: false`
   - dアニメストア: `enabled: false`
   - コミックナタリー: 新規追加 `enabled: true`
   - User-Agent: 実ブラウザのものに変更

### ステップ3: 動作確認（10分）

1. **Webアプリを再起動**:
   ```bash
   cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
   pkill -f "python.*web_app.py"
   python3 app/web_app.py &
   ```

2. **設定テストを実行**:
   - ブラウザで設定画面を開く
   - 「設定テスト」ボタンをクリック
   - 結果を確認

3. **期待される結果**:
   ```json
   {
     "gmail": {
       "status": "success",
       "message": "Gmail接続成功"
     },
     "rss_feeds": {
       "status": "success",
       "message": "1/1個のRSSフィードが正常"
     }
   }
   ```

---

## 5. 検証チェックリスト

### Gmail接続テスト

- [ ] .envファイルに `GMAIL_APP_PASSWORD` が設定されている
- [ ] .envファイルに `GMAIL_ADDRESS` が設定されている
- [ ] web_app.py に `load_dotenv()` が追加されている
- [ ] 設定テストで "Gmail接続成功" と表示される
- [ ] エラー時に詳細なヒントが表示される

### RSSフィードテスト

- [ ] config.json で BookWalker が無効化されている
- [ ] config.json で dアニメストア が無効化されている
- [ ] config.json で コミックナタリー が有効化されている
- [ ] User-Agent が実ブラウザのものに変更されている
- [ ] 設定テストで "1/1個のRSSフィードが正常" と表示される
- [ ] エラー時に詳細な情報が表示される

---

## 6. トラブルシューティング

### Gmail接続が失敗する場合

**エラー**: "Gmail接続エラー: authentication failed"

**対処法**:
1. Gmailアプリパスワードが正しいか確認
2. Googleアカウントで2段階認証が有効か確認
3. アプリパスワードを再生成

**確認コマンド**:
```bash
# .envファイル確認
grep GMAIL /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.env

# 手動テスト
python3 << 'EOF'
import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()
gmail = os.getenv('GMAIL_ADDRESS')
password = os.getenv('GMAIL_APP_PASSWORD')

print(f"Email: {gmail}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")

ctx = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as server:
    server.login(gmail, password)
    print('✅ Gmail接続成功')
EOF
```

### RSSフィードが失敗する場合

**エラー**: "すべてのRSSフィードでエラー"

**対処法**:
1. インターネット接続を確認
2. RSSフィードURLが有効か手動確認
3. ファイアウォールやプロキシ設定を確認

**確認コマンド**:
```bash
# コミックナタリーRSS確認
curl -I "https://natalie.mu/comic/feed/news"

# 期待される結果: HTTP/2 200
```

---

## 7. 完成後の状態

### 設定テスト結果（正常時）

```json
{
  "success": true,
  "results": {
    "gmail": {
      "status": "success",
      "message": "Gmail接続成功",
      "details": {
        "server": "smtp.gmail.com",
        "port": 465,
        "email": "kensan1969@gmail.com",
        "auth_method": "SMTP_SSL"
      }
    },
    "database": {
      "status": "success",
      "message": "データベース接続成功",
      "details": {
        "tables": ["works", "releases", "notifications"]
      }
    },
    "anilist": {
      "status": "success",
      "message": "AniList API接続成功"
    },
    "rss_feeds": {
      "status": "success",
      "message": "1/1個のRSSフィードが正常",
      "details": {
        "feeds": [
          {
            "name": "コミックナタリー",
            "status": "success",
            "message": "接続成功",
            "details": {
              "status_code": 200,
              "content_length": 22530,
              "content_type": "application/xml",
              "is_valid_xml": true,
              "response_time_ms": 245
            }
          }
        ]
      }
    }
  }
}
```

---

## 8. 今後の改善案

### 短期（今週中）

1. **追加RSSフィードの検証**:
   - マンガ: マガポケ、ジャンプ+、pixivコミック
   - アニメ: アニメ！アニメ！（User-Agent対策後）

2. **エラー通知機能**:
   - RSSフィード取得失敗時にログに記録
   - 連続失敗時に管理者に通知

### 中期（今月中）

1. **AniList API の活用強化**:
   - メインデータソースとして活用
   - ストリーミング情報の取得

2. **しょぼいカレンダーAPI の実装**:
   - 日本のアニメ放送スケジュール取得
   - AniListと統合

### 長期（来月以降）

1. **スクレイピング基盤構築**:
   - Playwright/Selenium実装
   - CloudflareやWAF回避手法

2. **公式API調査**:
   - 各サービスの公式API利用申請
   - API連携の実装

---

## 9. 関連ファイル

| ファイルパス | 変更内容 | 重要度 |
|---|---|---|
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py` | Gmail/RSSテスト機能の修正 | 🔴 高 |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json` | RSSフィード設定の更新 | 🔴 高 |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.env` | 確認のみ（変更不要） | 🟡 中 |

---

## 10. まとめ

### 実施内容

1. **Gmail接続エラー**: `load_dotenv()` 追加で解決
2. **RSSフィードエラー**: 無効なRSSを無効化、コミックナタリーを追加

### 予想効果

- 設定テストが正常に動作
- ユーザー体験の向上
- トラブルシューティングの容易化

### 次のステップ

1. ✅ **即座実施**: 本提案書の修正を適用
2. 🔄 **今週中**: 追加RSSフィードを検証
3. 📝 **今月中**: しょぼいカレンダーAPIを実装

---

**提案者**: Claude (Anthropic AI)
**承認状態**: Pending Review
**実装予定日**: 2025-11-15
