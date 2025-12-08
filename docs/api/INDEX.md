# API Documentation Index

MangaAnime Information Delivery System API仕様書へようこそ

## ドキュメント構成

### 1. [openapi.yaml](./openapi.yaml) ⭐必読
**OpenAPI 3.0仕様書 - 完全なAPI定義**

全APIエンドポイント、リクエスト/レスポンススキーマ、認証方式、エラーレスポンスの完全な定義。
Swagger UIやPostmanで直接インポート可能。

- 形式: YAML
- 行数: 1,559行
- サイズ: 41KB
- 対応ツール: Swagger UI, Postman, OpenAPI Generator

**推奨用途:**
- API仕様の完全な理解
- クライアントコードの自動生成
- API定義のバリデーション
- チーム間のAPI契約

---

### 2. [README.md](./README.md) 📖入門ガイド
**API使用ガイド - 実践的な使い方**

APIの使い方、認証方法、サンプルコード、トラブルシューティング。

**内容:**
- ✅ API仕様書の閲覧方法（Swagger UI等）
- ✅ 認証方式の詳細（セッション/APIキー）
- ✅ 主要エンドポイントのサンプルコード
- ✅ エラーハンドリング
- ✅ レート制限とページネーション
- ✅ クライアントライブラリの使い方
- ✅ トラブルシューティング

**対象読者:**
- APIを初めて使う開発者
- 統合を開始する開発チーム
- サポート担当者

---

### 3. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) ⚡クイックリファレンス
**API早見表 - すぐに使えるコード集**

よく使うエンドポイントのリクエスト/レスポンス例を一覧化。

**内容:**
- 🔹 認証（ログイン、APIキー）
- 🔹 作品管理（一覧、詳細、検索）
- 🔹 リリース情報（最近、今後）
- 🔹 ウォッチリスト（追加、削除、更新）
- 🔹 カレンダー（同期、イベント）
- 🔹 データ収集（手動実行、ステータス）
- 🔹 ヘルスチェック（Health, Metrics）
- 🔹 統計情報

**使い方:**
コピー＆ペーストで即利用可能なcurlコマンド集

---

### 4. [API_OVERVIEW.md](./API_OVERVIEW.md) 🏗️アーキテクチャ概要
**システム全体像 - 構成と設計**

システムアーキテクチャ、データフロー、セキュリティ、パフォーマンス最適化。

**内容:**
- 📊 システム構成図
- 📊 APIエンドポイント構成
- 📊 データフロー図
- 📊 認証・認可システム
- 📊 セキュリティ機能
- 📊 パフォーマンス最適化
- 📊 監視とログ
- 📊 エラーハンドリング

**対象読者:**
- システムアーキテクト
- インフラエンジニア
- セキュリティ担当者

---

## 読み進め方

### 初めての方
```
1. README.md で基本を理解
   ↓
2. QUICK_REFERENCE.md で実際に試す
   ↓
3. openapi.yaml で詳細を確認
```

### 統合開発者
```
1. openapi.yaml をSwagger UIで開く
   ↓
2. README.md の認証セクションを確認
   ↓
3. クライアントコードを自動生成
   ↓
4. QUICK_REFERENCE.md でテスト
```

### アーキテクト/上級開発者
```
1. API_OVERVIEW.md でシステム理解
   ↓
2. openapi.yaml で完全な仕様確認
   ↓
3. セキュリティとパフォーマンスを評価
```

---

## ツールとリソース

### API仕様書ビューワー

#### オンライン
- [Swagger Editor](https://editor.swagger.io/) - openapi.yamlをアップロード
- [Redoc](https://redocly.github.io/redoc/) - 美しいドキュメント表示

#### ローカル
```bash
# Swagger UI (Docker)
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/docs/openapi.yaml \
  -v $(pwd)/docs/api:/docs \
  swaggerapi/swagger-ui

# Redoc (Docker)
docker run -p 8080:80 \
  -e SPEC_URL=/spec/openapi.yaml \
  -v $(pwd)/docs/api:/usr/share/nginx/html/spec \
  redocly/redoc
```

### コード生成ツール

#### OpenAPI Generator
```bash
# Pythonクライアント
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g python \
  -o client/python

# TypeScriptクライアント
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g typescript-axios \
  -o client/typescript

# Javaクライアント
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g java \
  -o client/java
```

### バリデーションツール

```bash
# Spectral (OpenAPIリンター)
npm install -g @stoplight/spectral-cli
spectral lint docs/api/openapi.yaml

# swagger-cli
npm install -g swagger-cli
swagger-cli validate docs/api/openapi.yaml
```

### テストツール

#### Postman
1. Postmanを開く
2. Import → File → openapi.yamlを選択
3. コレクションが自動生成される

#### HTTPie
```bash
# インストール
pip install httpie

# 使用例
http POST localhost:5000/auth/login \
  username=admin password=pass123

http GET localhost:5000/api/works \
  X-API-Key:your-key
```

---

## API仕様バージョン

| バージョン | リリース日 | 主な変更点 |
|----------|----------|----------|
| 1.0.0    | 2025-12-08 | 初版リリース |
|          |            | - 全エンドポイント定義 |
|          |            | - 認証システム実装 |
|          |            | - ヘルスチェック追加 |
|          |            | - ウォッチリスト機能 |

---

## よくある質問 (FAQ)

### Q1: APIキーを取得するには?
A: Web UIにログイン後、/api-keys/ページでAPIキーを生成できます。

### Q2: レート制限はどのくらい?
A: デフォルトは1日200リクエスト、1時間50リクエストです。

### Q3: 認証方式はどれを使うべき?
A:
- Web UI統合: セッション認証
- 外部アプリ/CLI: APIキー認証

### Q4: エラーが発生した場合は?
A:
1. README.mdのトラブルシューティングセクションを確認
2. /health/detailedでシステム状態を確認
3. ログファイル（logs/）を確認

### Q5: OpenAPI仕様書を更新するには?
A: openapi.yamlを編集後、以下で検証:
```bash
spectral lint docs/api/openapi.yaml
```

---

## サンプルプロジェクト

### 最小限のクライアント実装

#### Python
```python
import requests

class MangaAnimeClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def get_works(self, work_type=None, limit=50):
        params = {"limit": limit}
        if work_type:
            params["type"] = work_type

        response = requests.get(
            f"{self.base_url}/api/works",
            headers=self.headers,
            params=params
        )
        return response.json()

# 使用例
client = MangaAnimeClient("http://localhost:5000", "your-api-key")
anime_list = client.get_works(work_type="anime")
print(f"Found {anime_list['count']} anime")
```

#### JavaScript/TypeScript
```typescript
class MangaAnimeClient {
  constructor(private baseUrl: string, private apiKey: string) {}

  async getWorks(type?: 'anime' | 'manga', limit = 50) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      ...(type && { type })
    });

    const response = await fetch(
      `${this.baseUrl}/api/works?${params}`,
      {
        headers: { 'X-API-Key': this.apiKey }
      }
    );

    return response.json();
  }
}

// 使用例
const client = new MangaAnimeClient('http://localhost:5000', 'your-api-key');
const animeList = await client.getWorks('anime');
console.log(`Found ${animeList.count} anime`);
```

---

## コントリビューション

### ドキュメントの改善
1. openapi.yamlの更新
2. 検証実行: `spectral lint docs/api/openapi.yaml`
3. プルリクエスト作成

### 新規エンドポイントの追加
1. app/web_app.pyまたはroutes/に実装
2. openapi.yamlに定義追加
3. QUICK_REFERENCE.mdにサンプル追加
4. README.mdに説明追加

---

## 関連ドキュメント

- [システム仕様書](../../CLAUDE.md)
- [セットアップガイド](../setup/)
- [運用手順書](../operations/)
- [トラブルシューティング](../troubleshooting/)

---

## サポート

### 技術的な質問
- GitHub Issues
- Email: support@example.com

### セキュリティ問題
- Email: security@example.com
- PGP Key: [公開鍵]

---

## ライセンス

MIT License

Copyright (c) 2025 MangaAnime Information Delivery System

---

**最終更新:** 2025-12-08
**作成者:** OpenAPI Documentation Specialist
**バージョン:** 1.0.0
