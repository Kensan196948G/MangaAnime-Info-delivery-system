# Annict API セットアップガイド

## 📌 概要

AnnictはアニメのトラッキングとデータベースサービスでREST API v1を提供しています。このガイドでは、Annict APIをこのシステムに統合する手順を説明します。

## 🔑 Personal Access Token の取得

### 1. Annictアカウント作成

https://annict.com/ にアクセスしてアカウントを作成してください（既にアカウントがある場合はログイン）。

### 2. Personal Access Token 発行

1. https://annict.com/settings/apps にアクセス
2. 「Personal Access Tokens」セクションで「新しいトークンを作成」をクリック
3. トークンの説明を入力（例：「MangaAnime情報配信システム」）
4. 必要な権限（スコープ）を選択：
   - ✅ `read` - 作品・エピソード・放送情報の取得
   - ✅ `read_record` - 視聴記録の取得（オプション）
5. 「作成」をクリック
6. 表示されたトークンをコピー（**一度しか表示されないので注意！**）

### 3. config.json に設定

`config.json`を開き、`annict`セクションを編集します：

```json
{
  "apis": {
    "annict": {
      "name": "Annict",
      "base_url": "https://api.annict.com/v1",
      "access_token": "YOUR_TOKEN_HERE",  // ← ここに取得したトークンを貼り付け
      "rate_limit": {
        "requests_per_minute": 60,
        "retry_delay_seconds": 3
      },
      "timeout_seconds": 30,
      "enabled": true,  // ← falseをtrueに変更
      "description": "Annict REST API v1 - 日本アニメ放送情報・作品データベース",
      "supports": ["anime"]
    }
  }
}
```

## ✅ テスト実行

トークンを設定したら、以下のコマンドでテストできます：

```bash
# Annictモジュール単体テスト
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules
python3 anime_annict.py
```

成功すると、以下のような出力が表示されます：

```
🔍 Testing Annict API integration...

📊 Results:
   Works: 50
   Programs: 25

📺 Sample work:
{
  "source": "annict",
  "source_id": "1234",
  "title": "作品タイトル",
  "title_kana": "サクヒンタイトル",
  ...
}
```

## 📊 取得可能なデータ

### 1. Works (作品情報) - `/v1/works`

- 作品タイトル（日本語、英語、かな）
- メディア種別（TV、OVA、映画など）
- エピソード数
- 放送シーズン
- 公式サイトURL
- Twitter、Wikipedia情報
- 画像データ
- 視聴者数、レビュー数

### 2. Programs (放送予定) - `/v1/me/programs`

- 放送開始日時
- 放送局（チャンネル）情報
- エピソード情報
- 再放送フラグ
- 作品との紐付けデータ

### 3. Episodes (エピソード) - `/v1/episodes`

- エピソード番号とタイトル
- 視聴記録数
- 前後エピソードの関連情報

## 🔧 カスタマイズ

### シーズン指定

特定のシーズンの作品を取得する場合：

```python
from modules.anime_annict import AnnictAPIClient

async with AnnictAPIClient(config) as client:
    # 2025年冬アニメ
    works = await client.get_current_season_works(season="2025-winter")

    # 2024年秋アニメ
    works = await client.get_current_season_works(season="2024-fall")
```

シーズン形式：
- `YYYY-winter` (1-3月)
- `YYYY-spring` (4-6月)
- `YYYY-summer` (7-9月)
- `YYYY-fall` (10-12月)

### 放送予定の取得期間

```python
from datetime import datetime, timedelta

async with AnnictAPIClient(config) as client:
    # 今日から7日間の放送予定
    start = datetime.now()
    programs = await client.get_programs(start_date=start)
```

## 🚨 トラブルシューティング

### エラー: "Invalid access token"

- トークンが正しく設定されているか確認
- トークンの有効期限が切れていないか確認
- https://annict.com/settings/apps でトークンを再発行

### エラー: "Rate limit exceeded"

- `requests_per_minute`を60以下に設定
- リクエスト間隔を調整

### エラー: "Endpoint not found"

- `base_url`が`https://api.annict.com/v1`であることを確認
- APIバージョンが最新か確認（ドキュメント：https://developers.annict.com/）

## 📚 参考リンク

- **Annict 公式サイト**: https://annict.com/
- **API ドキュメント**: https://developers.annict.com/docs/rest-api/v1
- **Personal Access Token 管理**: https://annict.com/settings/apps
- **Works エンドポイント**: https://developers.annict.com/docs/rest-api/v1/works
- **Programs エンドポイント**: https://developers.annict.com/docs/rest-api/v1/programs

## 💡 ヒント

1. **rate_limit設定**: Annictは60リクエスト/分を推奨
2. **データキャッシュ**: 同じデータを繰り返し取得しないよう、データベースに保存してキャッシュ
3. **エラーハンドリング**: トークン切れや接続エラーに備えて適切なエラー処理を実装
4. **定期更新**: cron等で定期的に最新データを取得（例：毎日1回）

---

**作成日**: 2025-11-16
**バージョン**: 1.0.0
