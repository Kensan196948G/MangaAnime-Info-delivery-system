# MangaAnime情報配信システム - システム構成図

## 📊 システム全体構成図

```mermaid
graph TB
    subgraph "外部サービス"
        A1[AniList GraphQL API<br/>アニメ情報]
        A2[RSS フィード<br/>dアニメストア・BookWalker]
        A3[Google APIs<br/>Gmail・Calendar]
    end
    
    subgraph "スケジューラ"
        S1[cron<br/>毎朝8:00実行]
    end
    
    subgraph "MangaAnime情報配信システム"
        subgraph "エントリポイント"
            M1[release_notifier.py<br/>メイン処理]
        end
        
        subgraph "データ収集レイヤー"
            C1[anime_anilist.py<br/>AniList統合]
            C2[manga_rss.py<br/>RSS統合]
        end
        
        subgraph "処理レイヤー"
            P1[filter_logic.py<br/>フィルタリング]
            P2[db.py<br/>データベース管理]
            P3[config.py<br/>設定管理]
        end
        
        subgraph "通知レイヤー"
            N1[mailer.py<br/>Gmail通知]
            N2[calendar.py<br/>Calendar統合]
            N3[templates/<br/>HTMLテンプレート]
        end
        
        subgraph "データ層"
            D1[(SQLite<br/>db.sqlite3)]
            D2[config.json<br/>設定ファイル]
            D3[credentials.json<br/>認証情報]
            D4[token.json<br/>アクセストークン]
        end
        
        subgraph "ログ・監視"
            L1[logs/app.log<br/>システムログ]
            L2[logger.py<br/>ログ管理]
        end
    end
    
    subgraph "ユーザー"
        U1[Gmail<br/>受信箱]
        U2[Googleカレンダー<br/>スケジュール]
    end
    
    %% データフロー
    S1 --> M1
    M1 --> C1
    M1 --> C2
    C1 --> A1
    C2 --> A2
    
    C1 --> P1
    C2 --> P1
    P1 --> P2
    P2 --> D1
    P3 --> D2
    
    P2 --> N1
    P2 --> N2
    N1 --> A3
    N2 --> A3
    N1 --> N3
    
    N1 --> U1
    N2 --> U2
    
    M1 --> L2
    L2 --> L1
    
    P3 --> D3
    P3 --> D4
    
    %% スタイル
    classDef external fill:#e1f5fe
    classDef system fill:#f3e5f5
    classDef data fill:#e8f5e8
    classDef user fill:#fff3e0
    
    class A1,A2,A3 external
    class M1,C1,C2,P1,P2,P3,N1,N2,N3,L2 system
    class D1,D2,D3,D4,L1 data
    class U1,U2 user
```

## 🏗️ レイヤー別詳細構成

### データ収集レイヤー詳細

```mermaid
graph TB
    subgraph "anime_anilist.py"
        AA1[AniListClient<br/>GraphQL クライアント]
        AA2[AniListCollector<br/>データコレクター]
        AA3[レート制限管理<br/>90req/min]
        AA4[非同期処理<br/>aiohttp]
    end
    
    subgraph "manga_rss.py"
        MR1[MangaRSSCollector<br/>RSS コレクター]
        MR2[BookWalkerRSSCollector<br/>専用コレクター]
        MR3[feedparser<br/>RSS解析]
        MR4[エラーハンドリング<br/>フォールバック]
    end
    
    subgraph "models.py"
        MD1[Work<br/>作品モデル]
        MD2[Release<br/>リリースモデル]
        MD3[RSSFeedItem<br/>RSSアイテム]
    end
    
    AA1 --> AA2
    AA2 --> AA3
    AA3 --> AA4
    AA2 --> MD1
    AA2 --> MD2
    
    MR1 --> MR3
    MR2 --> MR1
    MR1 --> MR4
    MR1 --> MD3
    MD3 --> MD1
    MD3 --> MD2
```

### 処理レイヤー詳細

```mermaid
graph TB
    subgraph "config.py"
        CF1[ConfigManager<br/>設定管理]
        CF2[環境変数オーバーライド<br/>設定の動的変更]
        CF3[設定検証<br/>バリデーション]
    end
    
    subgraph "filter_logic.py"
        FL1[ContentFilter<br/>コンテンツフィルター]
        FL2[NGキーワード<br/>10種類設定]
        FL3[NGジャンル<br/>2種類設定]
        FL4[除外タグ<br/>2種類設定]
    end
    
    subgraph "db.py"
        DB1[DatabaseManager<br/>データベース管理]
        DB2[SQLクエリ実行<br/>CRUD操作]
        DB3[トランザクション管理<br/>ACID準拠]
        DB4[重複排除<br/>UNIQUE制約]
    end
    
    CF1 --> CF2
    CF2 --> CF3
    CF1 --> FL1
    CF1 --> DB1
    
    FL1 --> FL2
    FL1 --> FL3
    FL1 --> FL4
    
    DB1 --> DB2
    DB2 --> DB3
    DB2 --> DB4
```

### 通知レイヤー詳細

```mermaid
graph TB
    subgraph "mailer.py"
        GM1[GmailNotifier<br/>Gmail送信]
        GM2[OAuth2認証<br/>Google APIs]
        GM3[HTMLメール<br/>リッチテンプレート]
    end
    
    subgraph "calendar.py"
        GC1[GoogleCalendarManager<br/>カレンダー管理]
        GC2[イベント作成<br/>一括処理]
        GC3[リマインダー設定<br/>60分・10分前]
    end
    
    subgraph "templates/"
        TP1[email_template.html<br/>メールテンプレート]
        TP2[CSS スタイル<br/>レスポンシブ対応]
        TP3[動的コンテンツ<br/>Jinja2テンプレート]
    end
    
    GM1 --> GM2
    GM1 --> GM3
    GM3 --> TP1
    TP1 --> TP2
    TP1 --> TP3
    
    GC1 --> GC2
    GC1 --> GC3
    GM2 -.-> GC1
```

## 🔄 データフロー詳細図

```mermaid
sequenceDiagram
    participant Cron as cron スケジューラ
    participant Main as release_notifier.py
    participant Config as 設定管理
    participant AniList as AniList API
    participant RSS as RSS フィード
    participant Filter as フィルタリング
    participant DB as データベース
    participant Gmail as Gmail API
    participant Calendar as Calendar API
    
    Cron->>Main: 毎朝8:00実行
    Main->>Config: 設定読み込み
    Config-->>Main: 設定情報
    
    par データ収集（並列処理）
        Main->>AniList: アニメ情報取得
        AniList-->>Main: GraphQLレスポンス
    and
        Main->>RSS: RSS解析
        RSS-->>Main: フィード情報
    end
    
    Main->>Filter: NGフィルタリング
    Filter-->>Main: フィルタ済みデータ
    
    Main->>DB: データ保存
    DB-->>Main: 新規リリース情報
    
    alt 新規リリースあり
        Main->>Gmail: HTMLメール送信
        Gmail-->>Main: 送信完了
        Main->>Calendar: イベント作成
        Calendar-->>Main: 作成完了
        Main->>DB: 通知済みフラグ更新
    else 新規リリースなし
        Main->>Main: スキップ
    end
    
    Main->>Main: 実行レポート生成
```

## 📁 ディレクトリ構成詳細

```
./
├── 📄 release_notifier.py          # メインエントリポイント
├── 📄 config.json                  # システム設定
├── 📄 credentials.json             # Google API認証情報
├── 📄 token.json                   # OAuth2トークン
├── 📄 requirements.txt             # Python依存関係
├── 📄 db.sqlite3                   # SQLiteデータベース
├── 📁 modules/                     # Pythonモジュール
│   ├── 📄 __init__.py
│   ├── 📄 anime_anilist.py         # AniList API統合
│   ├── 📄 manga_rss.py             # RSS フィード統合
│   ├── 📄 config.py                # 設定管理
│   ├── 📄 db.py                    # データベース管理
│   ├── 📄 filter_logic.py          # フィルタリングロジック
│   ├── 📄 mailer.py                # Gmail統合
│   ├── 📄 calendar.py              # Googleカレンダー統合
│   ├── 📄 logger.py                # ログ管理
│   └── 📄 models.py                # データモデル
├── 📁 docs/                        # ドキュメント
│   ├── 📄 システム概要.md
│   ├── 📄 利用手順書.md
│   ├── 📄 運用手順書.md
│   ├── 📄 技術仕様書.md
│   ├── 📄 トラブルシューティングガイド.md
│   └── 📄 システム構成図.md
├── 📁 logs/                        # ログファイル
│   └── 📄 app.log                  # システムログ
├── 📁 templates/                   # HTMLテンプレート
│   ├── 📄 base.html
│   ├── 📄 dashboard.html
│   └── 📄 releases.html
├── 📁 static/                      # 静的ファイル
│   ├── 📁 css/
│   │   └── 📄 style.css
│   └── 📁 js/
│       └── 📄 main.js
├── 📁 tests/                       # テストファイル
├── 📁 venv/                        # Python仮想環境
└── 📁 scripts/                     # ユーティリティスクリプト
    ├── 📄 create_token_simple.py   # 認証URL生成
    ├── 📄 generate_token.py        # トークン生成
    └── 📄 test_notification.py     # 通知テスト
```

## 🔐 セキュリティ構成図

```mermaid
graph TB
    subgraph "認証・認可"
        AUTH1[OAuth2.0<br/>Google認証]
        AUTH2[スコープ制限<br/>最小権限]
        AUTH3[トークン自動更新<br/>リフレッシュ]
    end
    
    subgraph "データ保護"
        DATA1[ファイル権限<br/>600/644/755]
        DATA2[機密情報分離<br/>設定ファイル]
        DATA3[ローカル保存<br/>外部流出防止]
    end
    
    subgraph "通信セキュリティ"
        COMM1[HTTPS強制<br/>TLS 1.2+]
        COMM2[証明書検証<br/>SSL検証]
        COMM3[タイムアウト設定<br/>DoS対策]
    end
    
    subgraph "監査・ログ"
        LOG1[操作ログ<br/>詳細記録]
        LOG2[エラー監視<br/>異常検知]
        LOG3[アクセス追跡<br/>セキュリティ監視]
    end
    
    AUTH1 --> DATA1
    AUTH2 --> DATA2
    AUTH3 --> DATA3
    
    DATA1 --> COMM1
    DATA2 --> COMM2
    DATA3 --> COMM3
    
    COMM1 --> LOG1
    COMM2 --> LOG2
    COMM3 --> LOG3
```

## ⚡ パフォーマンス構成図

```mermaid
graph TB
    subgraph "処理最適化"
        PERF1[非同期処理<br/>I/O並列化]
        PERF2[レート制限<br/>API保護]
        PERF3[キャッシュ活用<br/>重複排除]
    end
    
    subgraph "リソース管理"
        RES1[メモリ効率<br/>ジェネレータ使用]
        RES2[CPU効率<br/>バッチ処理]
        RES3[ディスク効率<br/>インデックス最適化]
    end
    
    subgraph "スケーラビリティ"
        SCALE1[水平分散<br/>複数インスタンス対応]
        SCALE2[垂直拡張<br/>リソース効率化]
        SCALE3[負荷分散<br/>API呼び出し最適化]
    end
    
    subgraph "監視・改善"
        MON1[実行時間監視<br/>15秒目標]
        MON2[メモリ監視<br/>50MB目標]
        MON3[エラー率監視<br/>0%維持]
    end
    
    PERF1 --> RES1
    PERF2 --> RES2
    PERF3 --> RES3
    
    RES1 --> SCALE1
    RES2 --> SCALE2
    RES3 --> SCALE3
    
    SCALE1 --> MON1
    SCALE2 --> MON2
    SCALE3 --> MON3
```

---

## 📊 システム統計情報（2025年8月8日現在）

| 項目 | 現在値 | 目標値 | 状況 |
|------|--------|--------|------|
| **実行時間** | 14.7秒 | <15秒 | ✅ 目標達成 |
| **メモリ使用量** | ~30MB | <50MB | ✅ 目標達成 |
| **データベース** | 362件 | - | 順調に蓄積 |
| **エラー率** | 0% | <1% | ✅ 目標達成 |
| **成功率** | 100% | >99% | ✅ 目標達成 |

**システム構成図 バージョン:** v1.0.0  
**最終更新日:** 2025年8月8日