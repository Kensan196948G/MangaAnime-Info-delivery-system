# Config.json 整合性修正 - 完了レポート

## 実施日時
2025-12-06

## タスク概要
config.jsonの設定値に存在した矛盾を解消し、整合性のある設定構造に再編成しました。

---

## 作成されたファイル一覧

### 1. バックアップファイル
- **ファイル名**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json.bak`
- **説明**: 修正前の元のconfig.jsonのバックアップ

### 2. 本番環境用設定テンプレート
- **ファイル名**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.production.json`
- **説明**: 本番環境用の拡張設定ファイル（セキュリティ、パフォーマンス設定含む）

### 3. JSONスキーマ定義
- **ファイル名**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.schema.json`
- **説明**: config.jsonの構造を定義するJSONスキーマ（バリデーション用）

### 4. ConfigHelperクラス
- **ファイル名**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules/config_helper.py`
- **説明**: 設定ファイルにアクセスするためのヘルパークラス（プロパティベース）

### 5. バリデーションスクリプト
- **ファイル名**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/validate_config.py`
- **説明**: config.jsonの検証と自動修正を行うスクリプト

### 6. ドキュメント
- **マイグレーションレポート**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/CONFIG_MIGRATION_REPORT.md`
- **コード更新ガイド**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/CODE_UPDATE_GUIDE.md`

---

## 実行手順

### 1. バリデーション＆修正の実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 scripts/validate_config.py
```

**実行結果:**
- config.jsonの矛盾をチェック
- 自動でバックアップを作成（config.json.bak）
- 整合性のある設定に修正
- 修正内容のサマリーを表示

### 2. ConfigHelperの動作確認

```bash
python3 modules/config_helper.py
```

**実行結果:**
- 現在のconfig.jsonを読み込み
- 主要な設定値を表示
- バリデーションチェックを実行

### 3. 既存コードの更新

```python
# Before: 古いアクセス方法
import json
with open('config.json') as f:
    config = json.load(f)
email = config['notification_email']

# After: ConfigHelperを使用
from modules.config_helper import get_config
config = get_config()
email = config.email_to
```

---

## 主な改善点

### 1. 矛盾の解消

#### メール通知
- **修正前**: トップレベルで`true`、notifications.emailで`false`
- **修正後**: 一貫して`true`に統一

#### カレンダー
- **修正前**: 3箇所で異なる値（`false`, `true`, `false`）
- **修正後**: 一貫して`true`に統一

### 2. 設定の統合

#### 重複排除
- `notification_email`: 3箇所 → `notifications.email.to`に統合
- `calendar_id`: 3箇所 → `notifications.calendar.calendar_id`に統合
- `calendar_enabled`: 3箇所 → `notifications.calendar.enabled`に統合

### 3. 論理的な階層構造

```
config.json
├── notifications/     # 通知関連（メール、カレンダー）
├── filters/          # フィルタリング（NGキーワード等）
├── sources/          # データソース（API、RSS）
├── database/         # データベース設定
├── logging/          # ログ設定
└── scheduling/       # スケジューリング設定
```

### 4. 拡張性の向上

新しく追加された設定項目:
- `notifications.email.send_time`: 送信時刻
- `notifications.calendar.color_by_genre`: ジャンル別色分け
- `notifications.calendar.reminder_minutes`: リマインダー設定
- `filters.min_rating`: 最低評価フィルタ
- `filters.excluded_genres`: 除外ジャンル
- `database.backup_enabled`: 自動バックアップ
- `logging.level`: ログレベル
- `scheduling.timezone`: タイムゾーン

---

## 新しいconfig.json構造

```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "to": "your-email@gmail.com",
      "subject_prefix": "[アニメ・マンガ情報]",
      "send_time": "08:00"
    },
    "calendar": {
      "enabled": true,
      "calendar_id": "primary",
      "event_title_format": "{title} {type} {number}",
      "color_by_genre": true,
      "reminder_minutes": [1440, 60]
    }
  },
  "filters": {
    "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"],
    "min_rating": null,
    "excluded_genres": []
  },
  "sources": {
    "anime": ["anilist", "syobocal"],
    "manga": ["bookwalker_rss", "magapoke_rss", "jumpbook_rss", "rakuten_kobo_rss"],
    "streaming": ["danime_rss", "anilist_streaming"]
  },
  "database": {
    "path": "db.sqlite3",
    "backup_enabled": true,
    "backup_interval_days": 7
  },
  "logging": {
    "level": "INFO",
    "file": "logs/system.log",
    "max_bytes": 10485760,
    "backup_count": 5
  },
  "scheduling": {
    "cron_expression": "0 8 * * *",
    "timezone": "Asia/Tokyo"
  }
}
```

---

## ConfigHelper使用例

### 基本的な使い方

```python
from modules.config_helper import get_config

# シングルトンインスタンスを取得
config = get_config()

# メール設定にアクセス
if config.email_enabled:
    send_email(
        to=config.email_to,
        subject=f"{config.email_subject_prefix} New Release",
        body=message
    )

# カレンダー設定にアクセス
if config.calendar_enabled:
    create_event(
        calendar_id=config.calendar_id,
        title=config.calendar_title_format.format(
            title="ワンピース",
            type="第",
            number="1100話"
        ),
        reminders=config.calendar_reminders
    )

# フィルタ設定にアクセス
for keyword in config.ng_keywords:
    if keyword in title:
        return False  # フィルタリング

# ドット記法でアクセス
value = config.get('notifications.email.enabled')
config.set('notifications.email.enabled', True)
```

### プロパティベースのアクセス

```python
config = get_config()

# 読み取り専用プロパティ
print(config.email_enabled)        # bool
print(config.email_to)             # str
print(config.calendar_id)          # str
print(config.ng_keywords)          # list
print(config.anime_sources)        # list
print(config.db_path)              # str
print(config.log_level)            # str

# 設定可能プロパティ（一部）
config.email_enabled = False
config.email_to = "new-email@example.com"
config.calendar_enabled = True

# 保存
config.save(backup=True)
```

---

## 更新が必要な既存ファイル

以下のファイルでconfig.jsonへのアクセス方法を更新する必要があります:

### 必須更新ファイル
1. `release_notifier.py` - メイン実行スクリプト
2. `modules/mailer.py` - メール送信処理
3. `modules/calendar.py` - カレンダー処理
4. `modules/filter_logic.py` - フィルタリング処理
5. `modules/db.py` - データベース処理

### 検索コマンド例

```bash
# 古い設定キーの使用箇所を検索
grep -rn "email_notifications_enabled" . --include="*.py"
grep -rn "notification_email" . --include="*.py"
grep -rn "calendar_enabled" . --include="*.py"
grep -rn "\['settings'\]" . --include="*.py"
```

---

## 本番環境への適用

### 開発環境
```bash
# 現在のconfig.jsonをそのまま使用
python3 scripts/validate_config.py
```

### 本番環境
```bash
# 本番用設定をコピー
sudo cp config.production.json /etc/manga-anime-system/config.json

# 本番用の値に編集
sudo vim /etc/manga-anime-system/config.json

# パーミッション設定
sudo chmod 600 /etc/manga-anime-system/config.json
sudo chown manga-anime:manga-anime /etc/manga-anime-system/config.json

# 検証
python3 -c "from modules.config_helper import ConfigHelper; \
            c = ConfigHelper('/etc/manga-anime-system/config.json'); \
            c.validate()"
```

---

## トラブルシューティング

### Q1: KeyError: 'email_notifications_enabled' が発生する

**A**: 古い設定キーを使用しています。以下のように修正してください:

```python
# Before
if config['email_notifications_enabled']:
    ...

# After
from modules.config_helper import get_config
config = get_config()
if config.email_enabled:
    ...
```

### Q2: 設定が反映されない

**A**: ConfigHelperインスタンスをリロードしてください:

```python
config = get_config()
config.reload()  # 設定ファイルを再読み込み
```

### Q3: JSONDecodeError が発生する

**A**: config.jsonの構文エラーです。以下で検証してください:

```bash
python3 -m json.tool config.json
```

---

## チェックリスト

- [x] config.json.bakの作成
- [x] config.jsonの整合性修正
- [x] config.production.jsonの作成
- [x] config.schema.jsonの作成
- [x] ConfigHelperクラスの実装
- [x] バリデーションスクリプトの作成
- [x] マイグレーションレポートの作成
- [x] コード更新ガイドの作成
- [ ] 既存コードの更新（modules/*.py）
- [ ] ユニットテストの作成
- [ ] 統合テストの実施

---

## 次のステップ

1. **既存コードの更新**
   - `modules/mailer.py`
   - `modules/calendar.py`
   - `modules/filter_logic.py`
   - `release_notifier.py`

2. **テストの作成**
   - ConfigHelperのユニットテスト
   - 設定ファイル読み込みの統合テスト

3. **CI/CDへの組み込み**
   - config.jsonのバリデーションをCIに追加
   - スキーマ検証の自動化

4. **ドキュメントの更新**
   - README.mdの更新
   - セットアップガイドの更新

---

## 参考リンク

- [マイグレーション詳細レポート](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/CONFIG_MIGRATION_REPORT.md)
- [コード更新ガイド](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/CODE_UPDATE_GUIDE.md)
- [JSONスキーマ定義](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.schema.json)

---

**作成日**: 2025-12-06
**作成者**: Fullstack Developer Agent
**レビュー状況**: Pending
